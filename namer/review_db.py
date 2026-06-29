"""
Small local review database for processing outcomes.

This is intentionally observational. It records what happened, but does not
change matching decisions and does not promote uncertain text matches.
"""

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, List, Optional

import orjson
from loguru import logger

from namer.command import Command
from namer.comparison_results import ComparisonResults
from namer.videophash import PerceptualHash

LOW_NAME_MATCH_TARGET = 90.0
NAME_MATCH_TARGET = 94.9
AMBIGUOUS_NAME_MATCH_MARGIN = 5.0


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)

    if hasattr(value, 'item'):
        return value.item()

    if isinstance(value, (set, tuple)):
        return list(value)

    raise TypeError


def _json_dumps(value: Any) -> str:
    return orjson.dumps(value, option=orjson.OPT_SERIALIZE_NUMPY, default=_json_default).decode('UTF-8')


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.execute('PRAGMA journal_mode=WAL')
    connection.execute('PRAGMA busy_timeout=5000')
    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS review_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path TEXT NOT NULL,
            current_path TEXT,
            final_path TEXT,
            original_parse_name TEXT,
            match_parse_name TEXT,
            parsed_site TEXT,
            parsed_date TEXT,
            parsed_name TEXT,
            extension TEXT,
            phash TEXT,
            oshash TEXT,
            status TEXT NOT NULL,
            reason TEXT,
            top_candidates TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute('CREATE INDEX IF NOT EXISTS idx_review_source_path ON review_items(source_path)')
    connection.execute('CREATE INDEX IF NOT EXISTS idx_review_status ON review_items(status)')
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS review_site_alias_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parsed_site TEXT NOT NULL,
            candidate_site TEXT NOT NULL,
            candidate_count INTEGER NOT NULL DEFAULT 0,
            best_name_match REAL,
            first_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(parsed_site, candidate_site)
        )
        """
    )
    connection.execute('CREATE INDEX IF NOT EXISTS idx_review_site_alias_suggestions_parsed_site ON review_site_alias_suggestions(parsed_site)')


def _candidate_summary(search_results: Optional[ComparisonResults]) -> str:
    if not search_results:
        return '[]'

    candidates: List[Dict[str, Any]] = []
    for result in search_results.results[:5]:
        looked_up = result.looked_up
        candidates.append(
            {
                'name': result.name,
                'name_match': result.name_match,
                'site_match': result.site_match,
                'date_match': result.date_match,
                'phash_distance': result.phash_distance,
                'phash_duration': result.phash_duration,
                'uuid': looked_up.uuid,
                'guid': looked_up.guid,
                'site': looked_up.site,
                'date': looked_up.date,
                'title': looked_up.name,
                'source_url': looked_up.source_url,
            }
        )

    return _json_dumps(candidates)


def classify_review_reason(command: Command, search_results: Optional[ComparisonResults]) -> str:
    """
    Classify why an item needs review without changing the matching outcome.
    """
    if not search_results or not search_results.results:
        return 'no_candidates'

    results = search_results.results
    top = results[0]
    parsed_file = search_results.fileinfo or command.parsed_file

    if top.site_match is False:
        if parsed_file and not parsed_file.date:
            return 'site_missing_or_overparsed'
        return 'site_mismatch'

    if parsed_file and not parsed_file.date:
        return 'date_missing'

    if top.date_match is False:
        return 'date_mismatch'

    if _has_close_competing_candidate(results):
        return 'ambiguous_candidates'

    if not top.name_match or top.name_match < LOW_NAME_MATCH_TARGET:
        return 'low_name_match'

    if top.name_match < NAME_MATCH_TARGET:
        return 'near_name_match'

    return 'no_verified_match'


def _has_close_competing_candidate(results: list) -> bool:
    if len(results) < 2:
        return False

    top = results[0]
    top_score = top.name_match or 0
    for candidate in results[1:5]:
        candidate_score = candidate.name_match or 0
        if (
            candidate.site_match == top.site_match
            and candidate.date_match == top.date_match
            and top_score - candidate_score <= AMBIGUOUS_NAME_MATCH_MARGIN
        ):
            return True

    return False


def _record_site_alias_suggestion(connection: sqlite3.Connection, command: Command, search_results: Optional[ComparisonResults], reason: str) -> None:
    if reason != 'site_mismatch' or not search_results or not search_results.results:
        return

    parsed_file = search_results.fileinfo or command.parsed_file
    parsed_site = parsed_file.site.strip() if parsed_file and parsed_file.site else ''
    candidate_site = search_results.results[0].looked_up.site.strip() if search_results.results[0].looked_up.site else ''
    if not parsed_site or not candidate_site or parsed_site.lower() == candidate_site.lower():
        return

    connection.execute(
        """
        INSERT INTO review_site_alias_suggestions (
            parsed_site, candidate_site, candidate_count, best_name_match
        )
        VALUES (?, ?, 1, ?)
        ON CONFLICT(parsed_site, candidate_site) DO UPDATE SET
            candidate_count = candidate_count + 1,
            best_name_match = max(coalesce(best_name_match, 0), coalesce(excluded.best_name_match, 0)),
            last_seen = CURRENT_TIMESTAMP
        """,
        (parsed_site, candidate_site, search_results.results[0].name_match),
    )


def record_review_item(
    command: Command,
    status: str,
    reason: str = '',
    search_results: Optional[ComparisonResults] = None,
    phash: Optional[PerceptualHash] = None,
    final_path: Optional[Path] = None,
) -> None:
    if not command.config.review_database_enabled:
        return

    try:
        parsed_file = command.parsed_file
        with closing(_connect(command.config.review_database_path)) as connection:
            _ensure_schema(connection)
            connection.execute(
                """
                INSERT INTO review_items (
                    source_path, current_path, final_path, original_parse_name, match_parse_name,
                    parsed_site, parsed_date, parsed_name, extension, phash, oshash,
                    status, reason, top_candidates
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(command.input_file) if command.input_file else None,
                    str(command.target_movie_file) if command.target_movie_file else None,
                    str(final_path) if final_path else None,
                    command.original_parse_name,
                    command.match_parse_name,
                    parsed_file.site if parsed_file else None,
                    parsed_file.date if parsed_file else None,
                    parsed_file.name if parsed_file else None,
                    parsed_file.extension if parsed_file else None,
                    str(phash.phash) if phash else None,
                    phash.oshash if phash else None,
                    status,
                    reason,
                    _candidate_summary(search_results),
                ),
            )
            _record_site_alias_suggestion(connection, command, search_results, reason)
            connection.commit()
    except Exception as error:  # pragma: no cover - review DB must never break processing
        logger.warning('Could not write review database item: {}', error)

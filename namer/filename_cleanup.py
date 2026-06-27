"""
Helpers for building a safer search name without renaming the source file.
"""

import re
from pathlib import PurePath
from typing import Iterable, Pattern

SEPARATOR_RE = re.compile(r'[._]+')
WHITESPACE_RE = re.compile(r'\s+')
EMPTY_BRACKETS_RE = re.compile(r'[\[\(\{]\s*[\]\)\}]')
RELEASE_TOKEN_RE = re.compile(
    r'(?i)(?<![a-z0-9])(?:'
    r'[0-9]{3,4}p|[0-9]k|[0-9]{2,3}fps|'
    r'uhd|fhd|hd|sd|hdr|sdr|dv|'
    r'proper|repack|internal|extended|uncut|remux|'
    r'rarbg|xpost|prt|xvx'
    r')(?![a-z0-9])'
)
ORPHAN_HYPHEN_RE = re.compile(r'(?:\s*-\s*){2,}')


def cleanup_filename_for_matching(filename: str, cleanup_regexes: Iterable[Pattern], normalize_separators: bool = True) -> str:
    """
    Return a cleaned file name for parsing and matching only.

    The caller keeps the real file path untouched. This gives noisy names a better
    search string while avoiding accidental renames or invented metadata.
    """
    path = PurePath(filename)
    cleaned = path.stem
    for cleanup_regex in cleanup_regexes:
        cleaned = cleanup_regex.sub(' ', cleaned)

    cleaned = RELEASE_TOKEN_RE.sub(' ', cleaned)
    cleaned = EMPTY_BRACKETS_RE.sub(' ', cleaned)

    if normalize_separators:
        cleaned = SEPARATOR_RE.sub(' ', cleaned)

    cleaned = EMPTY_BRACKETS_RE.sub(' ', cleaned)
    cleaned = ORPHAN_HYPHEN_RE.sub(' ', cleaned)
    cleaned = WHITESPACE_RE.sub(' ', cleaned).strip(' -._')
    if not cleaned:
        return filename

    return f'{cleaned}{path.suffix}'

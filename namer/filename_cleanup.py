"""
Helpers for building a safer search name without renaming the source file.
"""

import re
from pathlib import PurePath
from typing import Iterable, Pattern

SEPARATOR_RE = re.compile(r'[._]+')
WHITESPACE_RE = re.compile(r'\s+')
DASH_RE = re.compile(r'\s*-\s*')


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

    if normalize_separators:
        cleaned = SEPARATOR_RE.sub(' ', cleaned)
        cleaned = DASH_RE.sub(' - ', cleaned)

    cleaned = WHITESPACE_RE.sub(' ', cleaned).strip(' -._')
    if not cleaned:
        return filename

    return f'{cleaned}{path.suffix}'

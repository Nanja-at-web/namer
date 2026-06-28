"""
Parse string in to FileNamePart define in namer_types.
"""

import re
from dataclasses import dataclass
from pathlib import PurePath
from typing import List, Optional, Pattern

from loguru import logger

from namer.configuration import NamerConfig
from namer.videophash import PerceptualHash

DEFAULT_REGEX_TOKENS = '{_site}{_sep}{_optional_date}{_ts}{_name}{_dot}{_ext}'
YEAR_FIRST_DATE_RE = re.compile(r'(?<!\d)(?P<year>\d{2}|\d{4})[-._ ](?P<month>0?[1-9]|1[0-2])[-._ ](?P<day>0?[1-9]|[12]\d|3[01])(?!\d)')
DAY_FIRST_UNAMBIGUOUS_DATE_RE = re.compile(r'(?<!\d)(?P<day>1[3-9]|[23]\d|3[01])[-._ ](?P<month>0?[1-9]|1[0-2])[-._ ](?P<year>\d{4})(?!\d)')


@dataclass(init=False, repr=False, eq=True, order=False, unsafe_hash=True, frozen=False)
class FileInfo:
    """
    Represents info parsed from a file name, usually of a nzb, named something like:
    'EvilAngel.22.01.03.Carmela.Clutch.Fabulous.Anal.3-Way.XXX.2160p.MP4-GAYME-xpost'
    or
    'DorcelClub.20.12..Aya.Benetti.Megane.Lopez.And.Bella.Tina.2160p.MP4-GAYME-xpost'
    """

    # pylint: disable=too-many-instance-attributes

    site: Optional[str] = None
    """
    Site the file originated from, "DorcelClub", "EvilAngel", etc.
    """
    date: Optional[str] = None
    """
    formatted: YYYY-mm-dd
    """
    trans: bool = False
    """
    If the name originally started with an "TS" or "ts"
    it will be stripped out and placed in a separate location, aids in matching, usable to genre mark content.
    """
    name: Optional[str] = None
    """
    The remained of a file, usually between the date and video markers such as XXX, 4k, etc.   Heavy lifting
    occurs to match this to a scene name, perform names, or a combo of both.
    """
    extension: Optional[str] = None
    """
    The file's extension .mp4 or .mkv
    """
    source_file_name: Optional[str] = None
    """
    What was originally parsed.
    """
    source_file_stem: Optional[str] = None
    """
    What was originally parsed without parsed extension.
    """
    hashes: Optional[PerceptualHash] = None
    """
    File hashes.
    """

    def __str__(self) -> str:
        return f"""site: {self.site}
        date: {self.date}
        trans: {self.trans}
        name: {self.name}
        extension: {self.extension}
        original full name: {self.source_file_name}
        original full stem: {self.source_file_stem}
        hashes: {self.hashes.to_dict() if self.hashes else None}
        """


def name_cleaner(name: str, re_cleanup: List[Pattern]) -> str:
    """
    Given the name parts, following a date, but preceding the file extension, attempt to glean
    extra information and discard useless information for matching with the porndb.
    """
    for regex in re_cleanup:
        name = regex.sub('', name)

    name = name.replace('.', ' ')
    name = re.sub(r'[\[\(\{]\s*[\]\)\}]', ' ', name)
    name = ' '.join(name.split()).strip('-')

    return name


def parser_config_to_regex(tokens: str) -> Pattern[str]:
    """
    ``{_site}{_sep}{_optional_date}{_ts}{_name}{_dot}{_ext}``

    ``Site - YYYY.MM.DD - TS - name.mkv``

    ```
    _sep            r'[\\.\\- ]+'
    _site           r'(?P<site>[a-zA-Z0-9\\'\\.\\-\\ ]*?[a-zA-Z0-9]*?)'
    _date           r'(?P<year>[0-9]{2}(?:[0-9]{2})?)[\\.\\- ]+(?P<month>[0-9]{2})[\\.\\- ]+(?P<day>[0-9]{2})'
    _optional_date  r'(?:(?P<year>[0-9]{2}(?:[0-9]{2})?)[\\.\\- ]+(?P<month>[0-9]{2})[\\.\\- ]+(?P<day>[0-9]{2})[\\.\\- ]+)?'
    _ts             r'((?P<trans>[T|t][S|s])'+_sep+'){0,1}'
    _name           r'(?P<name>(?:.(?![0-9]{2,4}[\\.\\- ][0-9]{2}[\\.\\- ][0-9]{2}))*)'
    _dot            r'\\.'
    _ext            r'(?P<ext>[a-zA-Z0-9]{3,4})$'
    ```
    """

    _sep = r'[\.\- ]+'
    _site = r'(?P<site>.*?)'
    _date = r'(?P<year>[0-9]{2}(?:[0-9]{2})?)[\.\- ]+(?P<month>[0-9]{2})[\.\- ]+(?P<day>[0-9]{2})'
    _optional_date = r'(?:(?P<year>[0-9]{2}(?:[0-9]{2})?)[\.\- ]+(?P<month>[0-9]{2})[\.\- ]+(?P<day>[0-9]{2})[\.\- ]+)?'
    _ts = r'((?P<trans>[T|t][S|s])' + _sep + '){0,1}'
    _name = r'(?P<name>(?:.(?![0-9]{2,4}[\.\- ][0-9]{2}[\.\- ][0-9]{2}))*)'
    _dot = r'\.'
    _ext = r'(?P<ext>[a-zA-Z0-9]{3,4})$'
    regex = tokens.format_map(
        {
            '_site': _site,
            '_date': _date,
            '_optional_date': _optional_date,
            '_ts': _ts,
            '_name': _name,
            '_ext': _ext,
            '_sep': _sep,
            '_dot': _dot,
        }
    )
    return re.compile(regex)


def parse_file_name(filename: str, namer_config: NamerConfig) -> FileInfo:
    """
    Given an input name of the form site-yy.mm.dd-some.name.part.1.XXX.2160p.mp4,
    parses out the relevant information in to a structure form.
    """
    filename = replace_abbreviations(filename, namer_config)
    regex = parser_config_to_regex(namer_config.name_parser)
    path = PurePath(filename)
    fallback_date = _find_fallback_date_match(path.stem)
    file_name_parts = FileInfo()
    file_name_parts.extension = path.suffix[1:]
    match = regex.search(filename)
    if match:
        _apply_fileinfo_match(file_name_parts, match, namer_config, filename, path.stem)
    else:
        logger.debug('Could not parse target name which may be a file (or directory) name depending on settings and input: {}', filename)

    if fallback_date and (not file_name_parts.date or _site_looks_overparsed(file_name_parts.site)):
        parse_path = PurePath(f'{_remove_fallback_date(path.stem)}{path.suffix}')
        fallback_match = regex.search(parse_path.name)
        if fallback_match:
            _apply_fileinfo_match(file_name_parts, fallback_match, namer_config, filename, path.stem)
        file_name_parts.date = _format_date(fallback_date.group('year'), fallback_date.group('month'), fallback_date.group('day'))

    return file_name_parts


def _apply_fileinfo_match(file_name_parts: FileInfo, match: re.Match, namer_config: NamerConfig, source_file_name: str, source_file_stem: str) -> None:
    if match.groupdict().get('year'):
        file_name_parts.date = _format_date(match.group('year'), match.group('month'), match.group('day'))

    if match.groupdict().get('name'):
        file_name_parts.name = name_cleaner(match.group('name'), namer_config.re_cleanup)

    if match.groupdict().get('site'):
        file_name_parts.site = match.group('site')

    if match.groupdict().get('trans'):
        trans = match.group('trans')
        file_name_parts.trans = bool(trans and trans.strip().upper() == 'TS')

    file_name_parts.extension = match.group('ext')
    file_name_parts.source_file_name = source_file_name
    file_name_parts.source_file_stem = source_file_stem


def _site_looks_overparsed(site: Optional[str]) -> bool:
    return bool(site and '.' in site)


def find_fallback_date(text: str) -> Optional[str]:
    """
    Find a safe fallback date outside the configured parser position.

    This only accepts year-first dates or day-first dates where the day is greater
    than 12. Ambiguous dates such as 03.04.2018 are left alone because they could
    be either DMY or MDY depending on source naming conventions.
    """
    match = _find_fallback_date_match(text)
    if match:
        return _format_date(match.group('year'), match.group('month'), match.group('day'))

    return None


def _find_fallback_date_match(text: str) -> Optional[re.Match]:
    match = YEAR_FIRST_DATE_RE.search(text)
    if match:
        return match

    return DAY_FIRST_UNAMBIGUOUS_DATE_RE.search(text)


def _remove_fallback_date(text: str) -> str:
    text = YEAR_FIRST_DATE_RE.sub(' ', text, count=1)
    return DAY_FIRST_UNAMBIGUOUS_DATE_RE.sub(' ', text, count=1)


def _format_date(year: str, month: str, day: str) -> str:
    prefix = '20' if len(year) == 2 else ''
    return f'{prefix}{year}-{int(month):02d}-{int(day):02d}'


def replace_abbreviations(text: str, namer_config: NamerConfig):
    for abbreviation, full in namer_config.site_abbreviations.items():
        if abbreviation.match(text):
            text = abbreviation.sub(full, text, 1)
            break

    return text

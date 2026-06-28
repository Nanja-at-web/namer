"""
Test review_db.py
"""

import unittest
from types import SimpleNamespace

import numpy
import orjson

from namer.comparison_results import ComparisonResult, ComparisonResults, LookedUpFileInfo
from namer.fileinfo import FileInfo
from namer.review_db import _candidate_summary, classify_review_reason


class UnitTestAsTheDefaultExecution(unittest.TestCase):
    """
    Always test first.
    """

    def test_candidate_summary_serializes_numpy_scalars(self):
        looked_up = LookedUpFileInfo()
        looked_up.uuid = 'scene-uuid'
        looked_up.guid = 'scene-guid'
        looked_up.site = 'Example Site'
        looked_up.date = '2026-06-27'
        looked_up.name = 'Example Scene'

        results = ComparisonResults(
            [
                ComparisonResult(
                    name='Example Scene',
                    name_match=numpy.float64(99.5),
                    site_match=True,
                    date_match=True,
                    name_parts=None,
                    looked_up=looked_up,
                    phash_distance=numpy.int64(0),
                    phash_duration=True,
                )
            ],
            None,
        )

        candidates = orjson.loads(_candidate_summary(results))

        self.assertEqual(candidates[0]['name_match'], 99.5)
        self.assertEqual(candidates[0]['phash_distance'], 0)

    def test_classify_review_reason_no_candidates(self):
        self.assertEqual(classify_review_reason(_command(), ComparisonResults([], _fileinfo())), 'no_candidates')

    def test_classify_review_reason_site_mismatch_before_missing_date(self):
        results = ComparisonResults([_result(site_match=False, date_match=False, name_match=99)], _fileinfo(date=None))

        self.assertEqual(classify_review_reason(_command(), results), 'site_mismatch')

    def test_classify_review_reason_missing_date(self):
        results = ComparisonResults([_result(site_match=True, date_match=False, name_match=99)], _fileinfo(date=None))

        self.assertEqual(classify_review_reason(_command(), results), 'date_missing')

    def test_classify_review_reason_date_mismatch(self):
        results = ComparisonResults([_result(site_match=True, date_match=False, name_match=99)], _fileinfo(date='2026-06-27'))

        self.assertEqual(classify_review_reason(_command(), results), 'date_mismatch')

    def test_classify_review_reason_ambiguous_candidates(self):
        results = ComparisonResults(
            [
                _result(site_match=True, date_match=True, name_match=93),
                _result(site_match=True, date_match=True, name_match=91),
            ],
            _fileinfo(date='2026-06-27'),
        )

        self.assertEqual(classify_review_reason(_command(), results), 'ambiguous_candidates')

    def test_classify_review_reason_low_name_match(self):
        results = ComparisonResults([_result(site_match=True, date_match=True, name_match=80)], _fileinfo(date='2026-06-27'))

        self.assertEqual(classify_review_reason(_command(), results), 'low_name_match')


def _command(parsed_file=None):
    return SimpleNamespace(parsed_file=parsed_file)


def _fileinfo(site='Example Site', date='2026-06-27', name='Example Scene'):
    fileinfo = FileInfo()
    fileinfo.site = site
    fileinfo.date = date
    fileinfo.name = name
    fileinfo.extension = 'mp4'
    return fileinfo


def _result(site_match=True, date_match=True, name_match=99, site='Candidate Site'):
    looked_up = LookedUpFileInfo()
    looked_up.uuid = 'scene-uuid'
    looked_up.guid = 'scene-guid'
    looked_up.site = site
    looked_up.date = '2026-06-27'
    looked_up.name = 'Example Scene'
    return ComparisonResult(
        name='Example Scene',
        name_match=name_match,
        site_match=site_match,
        date_match=date_match,
        name_parts=None,
        looked_up=looked_up,
        phash_distance=None,
        phash_duration=None,
    )


if __name__ == '__main__':
    unittest.main()

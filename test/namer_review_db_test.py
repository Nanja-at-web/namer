"""
Test review_db.py
"""

import unittest
from types import SimpleNamespace

import numpy
import orjson

from namer.comparison_results import ComparisonResult, ComparisonResults, LookedUpFileInfo
from namer.fileinfo import FileInfo
from namer.review_db import _candidate_summary, _search_attempts_summary, _selected_candidate_summary, classify_review_reason


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
                    phash_duration_delta_seconds=numpy.int64(1),
                )
            ],
            None,
        )

        candidates = orjson.loads(_candidate_summary(results))

        self.assertEqual(candidates[0]['name_match'], 99.5)
        self.assertEqual(candidates[0]['phash_distance'], 0)
        self.assertEqual(candidates[0]['phash_duration_delta_seconds'], 1)
        self.assertIn('search_variant', candidates[0])
        self.assertIn('search_parse_name', candidates[0])
        self.assertIn('jav_code', candidates[0])
        self.assertIn('jav_code_match', candidates[0])

    def test_candidate_summary_records_jav_code_match(self):
        result = _result()
        result.jav_code = 'SSIS001'
        result.jav_code_match = True
        result.search_variant = 'jav_code:jav'
        result.search_scene_type = 'JAV'

        candidates = orjson.loads(_candidate_summary(ComparisonResults([result], None)))

        self.assertEqual(candidates[0]['jav_code'], 'SSIS001')
        self.assertTrue(candidates[0]['jav_code_match'])
        self.assertEqual(candidates[0]['search_variant'], 'jav_code:jav')

    def test_candidate_summary_respects_candidate_limit(self):
        results = ComparisonResults([_result(name_match=99), _result(name_match=98), _result(name_match=97)], None)

        candidates = orjson.loads(_candidate_summary(results, candidate_limit=2))

        self.assertEqual(len(candidates), 2)

    def test_search_attempts_summary_records_zero_result_variants(self):
        results = ComparisonResults(
            [],
            None,
            [
                {
                    'variant': 'overparsed_site_fallback:scene',
                    'scene_type': 'Scene',
                    'result_count': 0,
                }
            ],
        )

        attempts = orjson.loads(_search_attempts_summary(results))

        self.assertEqual(attempts[0]['variant'], 'overparsed_site_fallback:scene')
        self.assertEqual(attempts[0]['result_count'], 0)

    def test_selected_candidate_summary_records_actual_match(self):
        selected = _result(site_match=False, date_match=False, name_match=90)
        selected.phash_distance = numpy.int64(0)
        selected.phash_duration = True

        candidate = orjson.loads(_selected_candidate_summary(selected))

        self.assertEqual(candidate['name_match'], 90)
        self.assertEqual(candidate['phash_distance'], 0)
        self.assertEqual(candidate['uuid'], 'scene-uuid')

    def test_selected_candidate_summary_is_empty_without_match(self):
        self.assertEqual(orjson.loads(_selected_candidate_summary(None)), {})

    def test_classify_review_reason_no_candidates(self):
        self.assertEqual(classify_review_reason(_command(), ComparisonResults([], _fileinfo())), 'no_candidates')

    def test_classify_review_reason_site_missing_or_overparsed_before_missing_date(self):
        results = ComparisonResults([_result(site_match=False, date_match=False, name_match=99)], _fileinfo(date=None))

        self.assertEqual(classify_review_reason(_command(), results), 'site_missing_or_overparsed')

    def test_classify_review_reason_site_mismatch_with_date_anchor(self):
        results = ComparisonResults([_result(site_match=False, date_match=True, name_match=99)], _fileinfo(date='2026-06-27'))

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

    def test_classify_review_reason_near_name_match(self):
        results = ComparisonResults([_result(site_match=True, date_match=True, name_match=93)], _fileinfo(date='2026-06-27'))

        self.assertEqual(classify_review_reason(_command(), results), 'near_name_match')


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

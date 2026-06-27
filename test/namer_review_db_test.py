"""
Test review_db.py
"""

import unittest

import numpy
import orjson

from namer.comparison_results import ComparisonResult, ComparisonResults, LookedUpFileInfo
from namer.review_db import _candidate_summary


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


if __name__ == '__main__':
    unittest.main()

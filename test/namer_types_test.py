"""
Test namer_types.py
"""

import os
import sys
import unittest
from pathlib import Path

from loguru import logger

from namer.configuration import NamerConfig
from namer.configuration_utils import verify_configuration
from namer.name_formatter import PartialFormatter
from namer.comparison_results import ComparisonResult, ComparisonResults, LookedUpFileInfo, Performer
from namer.fileinfo import FileInfo
from test import utils


class UnitTestAsTheDefaultExecution(unittest.TestCase):
    """
    Always test first.
    """

    def __init__(self, method_name='runTest'):
        super().__init__(method_name)

        if not utils.is_debugging():
            logger.remove()

    def test_performer(self):
        """
        Test performer __str__
        """
        self.assertEqual(str(Performer(None, None)), 'Unknown')
        self.assertEqual(str(Performer('Name', None)), 'Name')
        self.assertEqual(str(Performer(None, disambiguation='Disambiguation')), 'Unknown (Disambiguation)')
        self.assertEqual(str(Performer('Name', disambiguation='Disambiguation')), 'Name (Disambiguation)')

    def test_default_no_config(self):
        """
        verify the default values of NamerConfig
        """
        config = NamerConfig()
        self.assertEqual(config.del_other_files, False)
        self.assertEqual(config.inplace_name, '{full_site} - {date} - {name} [WEBDL-{resolution}].{ext}')
        self.assertEqual(config.enabled_tagging, False)
        self.assertEqual(config.write_namer_log, False)
        self.assertEqual(config.enable_metadataapi_genres, False)
        self.assertEqual(config.default_genre, 'Adult')
        self.assertEqual(config.cleanup_enabled, True)
        self.assertEqual(config.phash_match_distance, 4)
        self.assertFalse(hasattr(config, 'dest_dir'))
        self.assertFalse(hasattr(config, 'failed_dir'))
        self.assertEqual(config.min_file_size, 300)
        self.assertEqual(config.language, None)
        if sys.platform != 'win32':
            self.assertEqual(config.set_uid, os.getuid())
            self.assertEqual(config.set_gid, os.getgid())
            self.assertEqual(config.set_dir_permissions, 775)
            self.assertEqual(config.set_file_permissions, 664)

    def test_phash_match_distance_is_configurable(self):
        looked_up = LookedUpFileInfo()
        result = ComparisonResult(
            name='Wrong text',
            name_match=10.0,
            site_match=False,
            date_match=False,
            name_parts=None,
            looked_up=looked_up,
            phash_distance=4,
            phash_duration=True,
        )
        results = ComparisonResults([result], None)

        self.assertFalse(result.is_match())
        self.assertTrue(result.is_match(target_distance=4))
        self.assertIsNone(results.get_match())
        self.assertEqual(results.get_match(target_distance=4), result)

        result.phash_duration = False
        self.assertFalse(result.is_match(target_distance=4))

    def test_exact_phash_match_keeps_best_text_candidate_when_duplicates_exist(self):
        looked_up = LookedUpFileInfo()
        result = ComparisonResult(
            name='Best text',
            name_match=99.0,
            site_match=False,
            date_match=False,
            name_parts=None,
            looked_up=looked_up,
            phash_distance=0,
            phash_duration=True,
        )
        competitor = ComparisonResult(
            name='Weaker text',
            name_match=90.0,
            site_match=False,
            date_match=False,
            name_parts=None,
            looked_up=looked_up,
            phash_distance=0,
            phash_duration=True,
        )
        results = ComparisonResults([result, competitor], None)

        self.assertEqual(results.get_match(target_distance=4), result)

    def test_phash_match_prefers_lower_distance_candidate(self):
        looked_up = LookedUpFileInfo()
        result = ComparisonResult(
            name='Higher text but weaker hash',
            name_match=99.0,
            site_match=False,
            date_match=False,
            name_parts=None,
            looked_up=looked_up,
            phash_distance=4,
            phash_duration=True,
        )
        competitor = ComparisonResult(
            name='Lower text but exact hash',
            name_match=90.0,
            site_match=False,
            date_match=False,
            name_parts=None,
            looked_up=looked_up,
            phash_distance=0,
            phash_duration=True,
        )
        results = ComparisonResults([result, competitor], None)

        self.assertEqual(results.get_match(target_distance=4), competitor)

    def test_phash_match_wins_over_verified_text_candidate(self):
        looked_up = LookedUpFileInfo()
        result = ComparisonResult(
            name='Verified text',
            name_match=97.0,
            site_match=True,
            date_match=True,
            name_parts=None,
            looked_up=looked_up,
            phash_distance=28,
            phash_duration=False,
        )
        competitor = ComparisonResult(
            name='Exact video fingerprint',
            name_match=90.0,
            site_match=False,
            date_match=False,
            name_parts=None,
            looked_up=looked_up,
            phash_distance=0,
            phash_duration=True,
        )
        results = ComparisonResults([result, competitor], None)

        self.assertEqual(results.get_match(target_distance=4), competitor)

    def test_no_date_text_match_requires_opt_in_and_unambiguous_site_title(self):
        fileinfo = FileInfo()
        fileinfo.site = 'Site'
        fileinfo.date = None
        fileinfo.name = 'Scene Title'

        looked_up = LookedUpFileInfo()
        result = ComparisonResult(
            name='Scene Title',
            name_match=98.0,
            site_match=True,
            date_match=False,
            name_parts=fileinfo,
            looked_up=looked_up,
            phash_distance=None,
            phash_duration=None,
        )
        results = ComparisonResults([result], fileinfo)

        self.assertFalse(result.is_match())
        self.assertIsNone(results.get_match())
        self.assertEqual(results.get_match(allow_text_similarity_auto_write=True), result)

    def test_no_date_text_match_rejects_close_competing_candidate(self):
        fileinfo = FileInfo()
        fileinfo.site = 'Site'
        fileinfo.date = None
        fileinfo.name = 'Scene Title'

        looked_up = LookedUpFileInfo()
        result = ComparisonResult(
            name='Scene Title',
            name_match=98.0,
            site_match=True,
            date_match=False,
            name_parts=fileinfo,
            looked_up=looked_up,
            phash_distance=None,
            phash_duration=None,
        )
        competitor = ComparisonResult(
            name='Scene Title 2',
            name_match=96.0,
            site_match=True,
            date_match=False,
            name_parts=fileinfo,
            looked_up=looked_up,
            phash_distance=None,
            phash_duration=None,
        )
        results = ComparisonResults([result, competitor], fileinfo)

        self.assertIsNone(results.get_match(allow_text_similarity_auto_write=True))

    def test_no_date_text_match_rejects_wrong_site_or_existing_source_date(self):
        no_date = FileInfo()
        no_date.site = 'Site'
        no_date.date = None
        no_date.name = 'Scene Title'

        with_date = FileInfo()
        with_date.site = 'Site'
        with_date.date = '2022-01-03'
        with_date.name = 'Scene Title'

        looked_up = LookedUpFileInfo()
        wrong_site = ComparisonResult(
            name='Scene Title',
            name_match=99.0,
            site_match=False,
            date_match=False,
            name_parts=no_date,
            looked_up=looked_up,
            phash_distance=None,
            phash_duration=None,
        )
        date_mismatch = ComparisonResult(
            name='Scene Title',
            name_match=99.0,
            site_match=True,
            date_match=False,
            name_parts=with_date,
            looked_up=looked_up,
            phash_distance=None,
            phash_duration=None,
        )

        self.assertIsNone(ComparisonResults([wrong_site], no_date).get_match(allow_text_similarity_auto_write=True))
        self.assertIsNone(ComparisonResults([date_mismatch], with_date).get_match(allow_text_similarity_auto_write=True))

    def test_formatter(self):
        """
        Verify that partial formatter can handle missing fields gracefully,
        and it's prefix, postfix, and infix capabilities work.
        """
        bad_fmt = '---'
        fmt = PartialFormatter(missing='', bad_fmt=bad_fmt)
        name = fmt.format('{name}{act: 1p}', name='scene1', act='act1')
        self.assertEqual(name, 'scene1 act1')
        name = fmt.format('{name}{act: 1p}', name='scene1', act=None)
        self.assertEqual(name, 'scene1')

        name = fmt.format('{name}{act: 1s}', name='scene1', act='act1')
        self.assertEqual(name, 'scene1act1 ')
        name = fmt.format('{name}{act: 1s}', name='scene1', act=None)
        self.assertEqual(name, 'scene1')

        name = fmt.format('{name}{act: 1i}', name='scene1', act='act1')
        self.assertEqual(name, 'scene1 act1 ')
        name = fmt.format('{name}{act: 1i}', name='scene1', act=None)
        self.assertEqual(name, 'scene1')

        name = fmt.format('{name}{act:_1i}', name='scene1', act='act1')
        self.assertEqual(name, 'scene1_act1_')

        name = fmt.format('{name}{act: >10}', name='scene1', act='act1')
        self.assertEqual(name, 'scene1      act1')

        name = fmt.format('{name:|title}{act:|upper}', name='scene1', act='act1')
        self.assertEqual(name, 'Scene1ACT1')

        with self.assertRaises(Exception) as error1:
            name = fmt.format('{name1}{act: >10}', name='scene1', act='act1')
            self.assertEqual(name, 'scene1      act1')
        self.assertTrue('name1' in str(error1.exception))
        self.assertTrue('all_performers' in str(error1.exception))

        self.assertEqual(fmt.format_field(format_spec='adsfadsf', value='fmt'), bad_fmt)

        with self.assertRaises(Exception) as error2:
            fmt1 = PartialFormatter(missing='', bad_fmt=None)  # type: ignore
            fmt1.format_field(format_spec='adsfadsf', value='fmt')
        self.assertTrue('Invalid format specifier' in str(error2.exception))

    def test_config_verification(self):
        """
        Verify config verification.
        """
        config = NamerConfig()
        success = verify_configuration(config, PartialFormatter())
        self.assertEqual(success, True)

        config = NamerConfig()
        config.watch_dir = Path('/not/a/real/path')
        success = verify_configuration(config, PartialFormatter())
        self.assertEqual(success, False)

        config = NamerConfig()
        config.work_dir = Path('/not/a/real/path')
        success = verify_configuration(config, PartialFormatter())
        self.assertEqual(success, False)

        config = NamerConfig()
        config.failed_dir = Path('/not/a/real/path')
        success = verify_configuration(config, PartialFormatter())
        self.assertEqual(success, False)

        config = NamerConfig()
        config.inplace_name = '{sitesadf} - {date}'
        success = verify_configuration(config, PartialFormatter())
        self.assertEqual(success, False)

        config1 = NamerConfig()
        config1.new_relative_path_name = '{whahha}/{site} - {date}'
        success = verify_configuration(config, PartialFormatter())
        self.assertEqual(success, False)


if __name__ == '__main__':
    unittest.main()

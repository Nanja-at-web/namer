"""
Test namer_metadataapi_test.py
"""

import io
import unittest
from types import SimpleNamespace
from unittest import mock

from loguru import logger

from namer.comparison_results import ComparisonResult, ComparisonResults, LookedUpFileInfo, SceneType
from namer.fileinfo import parse_file_name
from namer.command import make_command
from namer.metadataapi import _add_or_replace_result, _phash_duration_delta_seconds, _phash_duration_matches, build_overparsed_name_fallback, build_overparsed_name_fallbacks, build_site_repair_fallbacks, main, match
from test import utils
from test.utils import environment, sample_config


class UnitTestAsTheDefaultExecution(unittest.TestCase):
    """
    Always test first.
    """

    def __init__(self, method_name='runTest'):
        super().__init__(method_name)

        if not utils.is_debugging():
            logger.remove()

    def test_parse_response_metadataapi_net_dorcel(self):
        """
        Test parsing a stored response as a LookedUpFileInfo
        """
        with environment() as (_path, _parrot, config):
            name = parse_file_name('DorcelClub - 2021-12-23 - Aya.Benetti.Megane.Lopez.And.Bella.Tina.mp4', sample_config())
            results = match(name, config)
            self.assertEqual(len(results.results), 1)
            result = results.results[0]
            info = result.looked_up
            self.assertEqual(info.name, 'Peeping Tom')
            self.assertEqual(info.date, '2021-12-23')
            self.assertEqual(info.site, 'Dorcel Club')
            self.assertIsNotNone(info.description)
            if info.description is not None:
                self.assertRegex(info.description, r'kissing in a parking lot')
            self.assertEqual(info.source_url, 'https://dorcelclub.com/en/scene/85289/peeping-tom')
            self.assertIn(
                'bg-dorcel-club-peeping-tom',
                info.poster_url if info.poster_url else '',
            )
            self.assertEqual(info.performers[0].name, 'Ryan Benetti')
            self.assertEqual(info.performers[1].name, 'Aya Benetti')
            self.assertEqual(info.performers[2].name, 'Bella Tina')
            self.assertEqual(info.performers[3].name, 'Megane Lopez')
            self.assertEqual(info.new_file_name('{network}', config), '')

    def test_parse_response_metadataapi_net_dorcel_unicode_cruft(self):
        """
        Test parsing a stored response as a LookedUpFileInfo
        """
        with environment() as (_path, _parrot, config):
            # the "e"s in the string below are unicode е (0x435), not asci e (0x65).
            name = parse_file_name('DorcеlClub - 2021-12-23 - Aya.Bеnеtti.Mеgane.Lopеz.And.Bеlla.Tina.mp4', sample_config())
            results = match(name, config)
            self.assertEqual(len(results.results), 1)
            result = results.results[0]
            self.assertTrue(result.is_match())
            info = result.looked_up
            self.assertEqual(info.name, 'Peeping Tom')
            self.assertEqual(info.date, '2021-12-23')
            self.assertEqual(info.site, 'Dorcel Club')
            self.assertIsNotNone(info.description)
            if info.description is not None:
                self.assertRegex(info.description, r'kissing in a parking lot')
            self.assertEqual(info.source_url, 'https://dorcelclub.com/en/scene/85289/peeping-tom')
            self.assertIn(
                'bg-dorcel-club-peeping-tom.',
                info.poster_url if info.poster_url else '',
            )
            self.assertEqual(info.performers[0].name, 'Ryan Benetti')
            self.assertEqual(info.performers[1].name, 'Aya Benetti')
            self.assertEqual(info.performers[2].name, 'Bella Tina')
            self.assertEqual(info.performers[3].name, 'Megane Lopez')

    def test_call_metadataapi_net(self):
        """
        Test parsing a stored response as a LookedUpFileInfo
        """
        with environment() as (_path, _parrot, config):
            name = parse_file_name('EvilAngel.22.01.03.Carmela.Clutch.Fabulous.Anal.3-Way.XXX.mp4', sample_config())
            results = match(name, config)
            self.assertEqual(len(results.results), 1)
            result = results.results[0]
            self.assertTrue(result.date_match)
            self.assertTrue(result.site_match)
            self.assertGreaterEqual(result.name_match, 90.0)
            info = results.results[0].looked_up
            self.assertEqual(info.name, 'Carmela Clutch: Fabulous Anal 3-Way!')
            self.assertEqual(info.date, '2022-01-03')
            self.assertEqual(info.site, 'Evil Angel')
            self.assertEqual(info.network, 'Gamma Enterprises')
            self.assertIsNotNone(info.description)
            if info.description is not None:
                self.assertRegex(info.description, r'brunette Carmela Clutch positions her big, juicy')
            self.assertEqual(
                info.source_url,
                'https://evilangel.com/en/video/Carmela-Clutch-Fabulous-Anal-3-Way/198543',
            )
            self.assertIn('bg-evil-angel-carmela-clutch-fabulous-anal-3-way', info.poster_url if info.poster_url else '')
            self.assertEqual(info.performers[0].name, 'Carmela Clutch')
            self.assertEqual(info.performers[0].role, 'Female')
            self.assertEqual(info.performers[1].name, 'Francesca Le')
            self.assertEqual(info.performers[1].role, 'Female')
            self.assertEqual(info.performers[2].name, 'Mark Wood')
            self.assertEqual(info.performers[2].role, 'Male')
            self.assertEqual(info.new_file_name('{name}', config), 'Carmela Clutch Fabulous Anal 3-Way!')
            self.assertEqual(info.new_file_name('{year}', config), '2022')
            self.assertEqual(info.new_file_name('{network}', config), 'GammaEnterprises')

    def test_call_metadataapi_net2(self):
        """
        Test parsing a stored response as a LookedUpFileInfo
        """
        config = sample_config()
        config.min_file_size = 0
        with environment(config) as (_path, _parrot, config):
            name = parse_file_name('BrazzersExxtra.22.02.28.Marykate.Moss.Suck.Suck.Blow.XXX.1080p.MP4-WRB-xpost.mp4', sample_config())
            results = match(name, config)
            self.assertEqual(len(results.results), 1)
            result = results.results[0]
            self.assertTrue(result.date_match)
            self.assertTrue(result.site_match)
            self.assertGreaterEqual(result.name_match, 90.0)
            info = results.results[0].looked_up
            self.assertEqual(info.name, 'Suck, Suck, Blow')
            self.assertEqual(info.date, '2022-02-28')
            self.assertEqual(info.site, 'Brazzers Exxtra')

    def test_call_full_metadataapi_net(self):
        """
        Test parsing a full stored response (with tags) as a LookedUpFileInfo
        """
        with environment() as (_path, _parrot, config):
            name = parse_file_name('EvilAngel.22.01.03.Carmela.Clutch.Fabulous.Anal.3-Way.XXX.mp4', sample_config())
            results = match(name, config)
            self.assertEqual(len(results.results), 1)
            result = results.results[0]
            self.assertTrue(result.date_match)
            self.assertTrue(result.site_match)
            self.assertGreaterEqual(result.name_match, 90.0)
            info = results.results[0].looked_up
            self.assertEqual(info.name, 'Carmela Clutch: Fabulous Anal 3-Way!')
            self.assertEqual(info.date, '2022-01-03')
            self.assertEqual(info.site, 'Evil Angel')
            self.assertEqual(info.external_id, '198543')
            self.assertEqual(info.type, SceneType.SCENE)
            self.assertIsNotNone(info.description)
            if info.description is not None:
                self.assertRegex(info.description, r'brunette Carmela Clutch positions her big, juicy')
            self.assertEqual(info.source_url, 'https://evilangel.com/en/video/Carmela-Clutch-Fabulous-Anal-3-Way/198543')
            self.assertIsNotNone(info.poster_url)
            if info.poster_url is not None:
                self.assertRegex(info.poster_url, 'bg-evil-angel-carmela-clutch-fabulous-anal-3-way')
            self.assertEqual(info.performers[0].name, 'Carmela Clutch')
            self.assertEqual(info.performers[0].role, 'Female')
            self.assertEqual(info.performers[1].name, 'Francesca Le')
            self.assertEqual(info.performers[1].role, 'Female')
            self.assertEqual(info.performers[2].name, 'Mark Wood')
            self.assertEqual(info.performers[2].role, 'Male')

    def test_call_metadataapi_net_no_data(self):
        """
        verify an empty response from porndb is properly handled.
        """
        with environment() as (temp_dir, _parrot, config):
            filename: str = 'GoodAngel.22.01.03.Carmela.Clutch.Fabulous.Anal.3-Way.XXX.mp4'
            with open((temp_dir / filename), 'w'):
                pass
            command = make_command((temp_dir / filename), config)
            self.assertIsNotNone(command)
            if command is not None:
                results = match(command.parsed_file, config)
                self.assertEqual(len(results.results), 0)

    def test_call_metadataapi_net_no_message(self):
        """
        failed response (empty) is properly handled
        """
        config = sample_config()
        config.min_file_size = 0
        with environment() as (temp_dir, _parrot, config):
            filename: str = 'OkAngel.22.01.03.Carmela.Clutch.Fabulous.Anal.3-Way.XXX.mp4'
            with open((temp_dir / filename), 'w'):
                pass
            command = make_command((temp_dir / filename), config)
            self.assertIsNotNone(command)
            if command is not None:
                results = match(command.parsed_file, config)
                self.assertEqual(len(results.results), 0)

    def test_build_overparsed_name_fallback_combines_site_and_name(self):
        name = parse_file_name('New.Scene.Title.1080p.mp4', sample_config())

        fallback = build_overparsed_name_fallback(name)

        self.assertIsNotNone(fallback)
        if fallback is not None:
            self.assertIsNone(fallback.site)
            self.assertIsNone(fallback.date)
            self.assertEqual(fallback.name, 'New Scene Title')

    def test_build_overparsed_name_fallbacks_adds_name_only_variant(self):
        name = parse_file_name('New.Scene.Title.1080p.mp4', sample_config())

        fallbacks = build_overparsed_name_fallbacks(name)

        self.assertEqual([fallback.name for fallback in fallbacks], ['New Scene Title', 'Scene Title'])
        for fallback in fallbacks:
            self.assertIsNone(fallback.site)
            self.assertIsNone(fallback.date)

    def test_build_overparsed_name_fallbacks_normalizes_common_separators(self):
        name = parse_file_name('New+Scene_Title.Part.1080p.mp4', sample_config())

        fallbacks = build_overparsed_name_fallbacks(name)

        self.assertEqual(fallbacks[0].name, 'New Scene Title Part')

    def test_build_site_repair_fallbacks_uses_cleaned_original_stem(self):
        config = sample_config()
        name = parse_file_name('New.Scene.Title.Part.#big.WEBDL.x264.1080p.mp4', config)

        fallbacks = build_site_repair_fallbacks(name, config)

        self.assertGreater(len(fallbacks), 0)
        self.assertEqual(fallbacks[0].name, 'New Scene Title Part')
        for fallback in fallbacks:
            self.assertIsNone(fallback.site)
            self.assertIsNone(fallback.date)

    def test_overparsed_name_fallback_does_not_allow_text_auto_match(self):
        name = parse_file_name('New.Scene.Title.1080p.mp4', sample_config())
        fallback = build_overparsed_name_fallback(name)
        looked_up = LookedUpFileInfo()
        looked_up.site = 'Example Site'
        looked_up.date = '2026-06-29'
        looked_up.name = 'New Scene Title'
        result = ComparisonResult(
            name='New Scene Title',
            name_match=100,
            site_match=False,
            date_match=False,
            name_parts=fallback,
            looked_up=looked_up,
            phash_distance=None,
            phash_duration=None,
        )

        self.assertIsNone(ComparisonResults([result], fallback).get_match(allow_text_similarity_auto_write=True))

    def test_add_or_replace_result_keeps_better_same_uuid_candidate(self):
        existing = _comparison_result(uuid='same-uuid', name_match=0)
        better = _comparison_result(uuid='same-uuid', name_match=99, site_match=False, date_match=False, name_parts=build_overparsed_name_fallback(parse_file_name('New.Scene.Title.1080p.mp4', sample_config())))
        results = [existing]

        _add_or_replace_result(results, better)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name_match, 99)

    @mock.patch('namer.metadataapi.get_complete_metadataapi_net_fileinfo')
    @mock.patch('namer.metadataapi.__metadata_api_lookup')
    def test_match_loads_complete_metadata_for_actual_matched_candidate(self, mock_lookup, mock_complete):
        config = sample_config()
        fileinfo = parse_file_name('Example.Scene.Title.mp4', config)
        text_only_candidate = _comparison_result(uuid='text-uuid', name_match=100, site_match=True, date_match=False, name_parts=fileinfo)
        phash_candidate = _comparison_result(uuid='phash-uuid', name_match=80, site_match=False, date_match=False, name_parts=fileinfo)
        phash_candidate.phash_distance = 4
        phash_candidate.phash_duration = True

        complete = LookedUpFileInfo()
        complete.uuid = 'phash-uuid'
        complete.name = 'Complete PHASH Match'

        mock_lookup.return_value = [text_only_candidate, phash_candidate]
        mock_complete.return_value = complete

        results = match(fileinfo, config)

        mock_complete.assert_called_once_with(fileinfo, 'phash-uuid', config)
        self.assertEqual(results.results[0].looked_up.uuid, 'text-uuid')
        self.assertEqual(results.results[1].looked_up.name, 'Complete PHASH Match')

    @mock.patch('namer.metadataapi.__get_metadataapi_net_fileinfo')
    def test_match_records_search_attempts_without_candidates(self, mock_lookup):
        config = sample_config()
        fileinfo = parse_file_name('Example.Scene.Title.mp4', config)
        mock_lookup.return_value = []

        results = match(fileinfo, config)

        self.assertEqual(results.results, [])
        self.assertGreater(len(results.search_attempts), 0)
        self.assertEqual(results.search_attempts[0]['result_count'], 0)
        self.assertIn('variant', results.search_attempts[0])

    @mock.patch('namer.metadataapi.__get_metadataapi_net_fileinfo')
    def test_match_does_not_duplicate_phash_no_name_search_attempts(self, mock_lookup):
        config = sample_config()
        fileinfo = parse_file_name('Example.Scene.Title.mp4', config)
        phash = SimpleNamespace(phash='abc123', duration=1200)
        mock_lookup.return_value = []

        results = match(fileinfo, config, phash=phash)

        variants = [attempt['variant'] for attempt in results.search_attempts]
        self.assertIn('primary:scene:phash', variants)
        self.assertIn('site_repair:scene', variants)
        self.assertNotIn('primary:scene:phash:no_name', variants)

    @mock.patch('namer.metadataapi.__get_metadataapi_net_fileinfo')
    def test_match_records_site_repair_search_attempts(self, mock_lookup):
        config = sample_config()
        fileinfo = parse_file_name('New.Scene.Title.mp4', config)
        mock_lookup.return_value = []

        results = match(fileinfo, config)

        variants = [attempt['variant'] for attempt in results.search_attempts]
        self.assertIn('site_repair:scene', variants)
        self.assertIn('site_repair:movie', variants)

    @mock.patch('namer.metadataapi.__get_metadataapi_net_fileinfo')
    def test_match_skips_primary_site_only_for_site_repair_candidate(self, mock_lookup):
        config = sample_config()
        fileinfo = parse_file_name('New.Scene.Title.mp4', config)
        mock_lookup.return_value = []

        results = match(fileinfo, config)

        variants = [attempt['variant'] for attempt in results.search_attempts]
        self.assertIn('primary:scene', variants)
        self.assertIn('site_repair:scene', variants)
        self.assertNotIn('primary:scene:no_name', variants)
        self.assertNotIn('primary:movie:no_name', variants)

    @mock.patch('namer.metadataapi.__get_metadataapi_net_fileinfo')
    def test_match_keeps_primary_site_only_when_date_is_present(self, mock_lookup):
        config = sample_config()
        fileinfo = parse_file_name('Example.2026.07.04.Scene.Title.mp4', config)
        mock_lookup.return_value = []

        results = match(fileinfo, config)

        variants = [attempt['variant'] for attempt in results.search_attempts]
        self.assertIn('primary:scene:no_name', variants)

    def test_phash_duration_tolerance_allows_small_difference(self):
        self.assertTrue(_phash_duration_matches(1201, 1200, tolerance_seconds=2))
        self.assertTrue(_phash_duration_matches(1198, 1200, tolerance_seconds=2))
        self.assertFalse(_phash_duration_matches(1197, 1200, tolerance_seconds=2))

    def test_phash_duration_delta_seconds(self):
        self.assertEqual(_phash_duration_delta_seconds(1197, 1200), 3)
        self.assertEqual(_phash_duration_delta_seconds(1201, 1200), 1)

    def test_phash_duration_tolerance_keeps_missing_candidate_duration_compatible(self):
        self.assertTrue(_phash_duration_matches(None, 1200, tolerance_seconds=2))
        self.assertIsNone(_phash_duration_delta_seconds(None, 1200))

    @mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_main_metadataapi_net(self, mock_stdout):
        """
        Test parsing a full stored response (with tags) as a LookedUpFileInfo
        """
        with environment() as (temp_dir, _parrot, config):
            filename: str = 'EvilAngel.22.01.03.Carmela.Clutch.Fabulous.Anal.3-Way.XXX.mp4'
            tmp_file = temp_dir / filename
            with open(tmp_file, 'w'):
                pass
            main(['-f', str(tmp_file), '-c', str(config.config_file)])
            self.assertIn('Evil Angel - 2022-01-03 - Carmela Clutch Fabulous Anal 3-Way! [WEBDL-].mp4', mock_stdout.getvalue())

def _comparison_result(uuid='scene-uuid', name_match=99, site_match=False, date_match=False, name_parts=None):
    looked_up = LookedUpFileInfo()
    looked_up.uuid = uuid
    looked_up.site = 'Example Site'
    looked_up.date = '2026-06-29'
    looked_up.name = 'New Scene Title'
    return ComparisonResult(
        name='New Scene Title' if name_match else '',
        name_match=name_match,
        site_match=site_match,
        date_match=date_match,
        name_parts=name_parts,
        looked_up=looked_up,
        phash_distance=None,
        phash_duration=None,
    )


if __name__ == '__main__':
    unittest.main()

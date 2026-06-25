"""
Tests for internal filename cleanup before matching.
"""

from pathlib import Path

from namer.command import make_command
from namer.filename_cleanup import cleanup_filename_for_matching
from test.utils import sample_config


def test_cleanup_filename_for_matching_removes_hash_tags_and_release_markers():
    config = sample_config()
    cleaned = cleanup_filename_for_matching(
        'EvilAngel.22.01.03.Carmela.Clutch.Fabulous.Anal.XXX.#big.WEBDL.x264.mp4',
        config.cleanup_remove_regex,
    )

    assert cleaned == 'EvilAngel 22 01 03 Carmela Clutch Fabulous Anal XXX.mp4'


def test_make_command_uses_cleaned_name_but_preserves_original(tmp_path: Path):
    config = sample_config()
    config.cleanup_enabled = True
    config.min_file_size = 0

    target = tmp_path / 'EvilAngel.22.01.03.Carmela.Clutch.Fabulous.Anal.XXX.#big.WEBDL.x264.mp4'
    target.write_text('x')

    command = make_command(target, config)

    assert command is not None
    assert command.original_parse_name == target.name
    assert command.match_parse_name == 'EvilAngel 22 01 03 Carmela Clutch Fabulous Anal XXX.mp4'
    assert command.parsed_file is not None
    assert command.parsed_file.source_file_name == target.name
    assert command.parsed_file.name == 'Carmela Clutch Fabulous Anal'

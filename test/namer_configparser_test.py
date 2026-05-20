"""
Tests namer_configparser
"""

from configupdater import ConfigUpdater
import os
import unittest
from importlib import resources
from pathlib import Path
import tempfile
from unittest.mock import patch
from io import StringIO
from contextlib import redirect_stdout

from loguru import logger

import namer.__main__
from namer.configuration import NamerConfig
from namer.configuration_utils import default_config, from_config, to_ini
from test import utils


class UnitTestAsTheDefaultExecution(unittest.TestCase):
    """
    Always test first.
    """

    def __init__(self, method_name='runTest'):
        super().__init__(method_name)

        if not utils.is_debugging():
            logger.remove()

    def test_configuration(self) -> None:
        mount_path = Path(__file__).resolve().parent / 'mnt' / 'nas'
        updater = ConfigUpdater(allow_no_value=True)
        config_str = ''
        if hasattr(resources, 'files'):
            config_str = resources.files('namer').joinpath('namer.cfg.default').read_text()
        elif hasattr(resources, 'read_text'):
            config_str = resources.read_text('namer', 'namer.cfg.default')
        updater.read_string(config_str)
        namer_config = from_config(updater, NamerConfig())
        namer_config.config_updater = updater
        namer_config.sites_with_no_date_info = ['badsite']
        namer_config.is_setup_complete = True
        namer_config.setup_mode = 'wizard'
        namer_config.storage_mode = 'nfs'
        namer_config.nas_host = 'nas.local'
        namer_config.nas_share = 'movies'
        namer_config.nas_mount_path = mount_path
        namer_config.nas_mount_options = 'rw'
        ini_content = to_ini(namer_config)
        self.assertIn('sites_with_no_date_info = badsite', ini_content.splitlines())
        self.assertIn('[setup]', ini_content.splitlines())
        self.assertIn('is_setup_complete = True', ini_content.splitlines())
        self.assertIn('setup_mode = wizard', ini_content.splitlines())
        self.assertIn('storage_mode = nfs', ini_content.splitlines())
        self.assertIn(f'nas_mount_path = {mount_path}', ini_content.splitlines())

        updated = ConfigUpdater(allow_no_value=True)
        lines = ini_content.splitlines()
        lines.remove('sites_with_no_date_info = badsite')
        files_no_sites_with_no_date_info = '\n'.join(lines)

        updated.read_string(files_no_sites_with_no_date_info)
        double_read = NamerConfig()
        double_read = from_config(updated, double_read)
        self.assertEqual(double_read.sites_with_no_date_info, [])
        updated.read_string(ini_content)
        double_read = from_config(updated, double_read)
        self.assertIn('badsite', double_read.sites_with_no_date_info)
        self.assertTrue(double_read.is_setup_complete)
        self.assertEqual(double_read.setup_mode, 'wizard')
        self.assertEqual(double_read.storage_mode, 'nfs')
        self.assertEqual(double_read.nas_host, 'nas.local')
        self.assertEqual(double_read.nas_share, 'movies')
        self.assertEqual(double_read.nas_mount_path, mount_path.resolve())
        self.assertEqual(double_read.nas_mount_options, 'rw')

        updated.read_string(files_no_sites_with_no_date_info)
        double_read = from_config(updated, double_read)
        self.assertIn('badsite', double_read.sites_with_no_date_info)

    def test_explicit_blank_values_clear_previous_values(self) -> None:
        packaged_defaults = ConfigUpdater(allow_no_value=True)
        config_str = ''
        if hasattr(resources, 'files'):
            config_str = resources.files('namer').joinpath('namer.cfg.default').read_text()
        elif hasattr(resources, 'read_text'):
            config_str = resources.read_text('namer', 'namer.cfg.default')
        packaged_defaults.read_string(config_str)

        defaults = from_config(packaged_defaults, NamerConfig())
        updater = ConfigUpdater(allow_no_value=True)
        updater.read_string(
            """
[setup]
nas_host = nas.local
nas_share = movies
nas_mount_path = /mnt/nas
nas_mount_options = rw

[namer]
min_file_size = 123
trailer_location = trailers
sites_with_no_date_info = badsite
database_path = ./custom-database
update_permissions_ownership = False

[watchdog]
port = 1234
"""
        )

        namer_config = from_config(updater, NamerConfig())

        cleared = ConfigUpdater(allow_no_value=True)
        cleared.read_string(
            """
[setup]
nas_host =
nas_share =
nas_mount_path =
nas_mount_options =

[namer]
min_file_size =
trailer_location =
sites_with_no_date_info =
database_path =
update_permissions_ownership =

[watchdog]
port =
"""
        )

        reloaded = from_config(cleared, namer_config)

        self.assertEqual(reloaded.nas_host, '')
        self.assertEqual(reloaded.nas_share, '')
        self.assertEqual(reloaded.nas_mount_path, defaults.nas_mount_path.resolve())
        self.assertEqual(reloaded.nas_mount_options, defaults.nas_mount_options)
        self.assertEqual(reloaded.min_file_size, defaults.min_file_size)
        self.assertEqual(reloaded.trailer_location, '')
        self.assertEqual(reloaded.sites_with_no_date_info, [])
        self.assertEqual(reloaded.database_path, defaults.database_path.resolve())
        self.assertEqual(reloaded.update_permissions_ownership, defaults.update_permissions_ownership)
        self.assertEqual(reloaded.port, defaults.port)

    def test_default_config_uses_lxc_path_before_legacy_paths(self) -> None:
        home_dir = Path('/fake-home')
        home_config = home_dir / '.namer.cfg'
        lxc_config = Path('/etc/namer/namer.cfg')

        def fake_is_file(path_self: Path) -> bool:
            return path_self in {home_config, lxc_config}

        def fake_read(updater: ConfigUpdater, filename, encoding='UTF-8'):
            path = Path(filename)
            if path == lxc_config:
                updater.read_string('[watchdog]\nport = 6123\n')
            elif path == home_config:
                updater.read_string('[watchdog]\nport = 7123\n')
            return [str(path)]

        with patch.dict('os.environ', {}, clear=True):
            with patch('namer.configuration_utils.sys.platform', 'linux'):
                with patch('namer.configuration.sys.platform', 'linux'):
                    with patch('namer.configuration.os.getuid', return_value=1000, create=True):
                        with patch('namer.configuration.os.getgid', return_value=1000, create=True):
                            with patch('namer.configuration_utils.Path.home', return_value=home_dir):
                                with patch('namer.configuration_utils.Path.is_file', autospec=True, side_effect=fake_is_file):
                                    with patch.object(ConfigUpdater, 'read', autospec=True, side_effect=fake_read):
                                        config = default_config()

        self.assertEqual(config.port, 6123)

    def test_default_config_skips_lxc_path_on_windows(self) -> None:
        home_dir = Path('/fake-home')
        home_config = home_dir / '.namer.cfg'
        lxc_config = Path('/etc/namer/namer.cfg')

        def fake_is_file(path_self: Path) -> bool:
            return path_self in {home_config, lxc_config}

        def fake_read(updater: ConfigUpdater, filename, encoding='UTF-8'):
            path = Path(filename)
            if path == lxc_config:
                updater.read_string('[watchdog]\nport = 6123\n')
            elif path == home_config:
                updater.read_string('[watchdog]\nport = 7123\n')
            return [str(path)]

        with patch.dict('os.environ', {}, clear=True):
            with patch('namer.configuration_utils.sys.platform', 'win32'):
                with patch('namer.configuration_utils.Path.home', return_value=home_dir):
                    with patch('namer.configuration_utils.Path.is_file', autospec=True, side_effect=fake_is_file):
                        with patch.object(ConfigUpdater, 'read', autospec=True, side_effect=fake_read):
                            config = default_config()

        self.assertEqual(config.port, 7123)

    def test_create_default_config_if_missing_creates_local_default_file(self) -> None:
        output = StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / '.namer.cfg'
            previous_cwd = Path.cwd()
            os.chdir(tmpdir)
            try:
                with redirect_stdout(output):
                    namer.__main__.create_default_config_if_missing()
            finally:
                os.chdir(previous_cwd)

            self.assertTrue(config_file.is_file())

        self.assertIn('Creating default config file here: .namer.cfg', output.getvalue())

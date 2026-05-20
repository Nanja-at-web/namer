"""
Tests setup configuration defaults and parsing.
"""

from importlib import resources
from pathlib import Path
import tempfile
import unittest

from configupdater import ConfigUpdater
from loguru import logger

from namer.configuration import NamerConfig
from namer.configuration_utils import default_config, from_config
from test import utils


class UnitTestSetupConfiguration(unittest.TestCase):
    """
    Always test first.
    """

    def __init__(self, method_name='runTest'):
        super().__init__(method_name)

        if not utils.is_debugging():
            logger.remove()

    def test_setup_defaults_are_loaded_and_exposed(self) -> None:
        updater = ConfigUpdater(allow_no_value=True)
        config_str = ''
        if hasattr(resources, 'files'):
            config_str = resources.files('namer').joinpath('namer.cfg.default').read_text()
        elif hasattr(resources, 'read_text'):
            config_str = resources.read_text('namer', 'namer.cfg.default')
        updater.read_string(config_str)

        namer_config = from_config(updater, NamerConfig())
        config_dict = namer_config.to_dict()

        self.assertFalse(namer_config.is_setup_complete)
        self.assertEqual(namer_config.setup_mode, 'wizard')
        self.assertEqual(namer_config.storage_mode, 'nfs')
        self.assertEqual(namer_config.nas_host, '')
        self.assertEqual(namer_config.nas_share, '')
        self.assertEqual(namer_config.nas_mount_path, Path('/mnt/nas').resolve())
        self.assertEqual(namer_config.nas_mount_options, 'defaults,_netdev')
        self.assertFalse(config_dict['Setup Config']['is_setup_complete'])
        self.assertEqual(config_dict['Setup Config']['setup_mode'], 'wizard')
        self.assertEqual(config_dict['Setup Config']['storage_mode'], 'nfs')
        self.assertEqual(config_dict['Setup Config']['nas_host'], '')
        self.assertEqual(config_dict['Setup Config']['nas_share'], '')
        self.assertEqual(config_dict['Setup Config']['nas_mount_path'], str(Path('/mnt/nas').resolve()))
        self.assertEqual(config_dict['Setup Config']['nas_mount_options'], 'defaults,_netdev')

    def test_setup_nas_mount_path_is_resolved_from_config(self) -> None:
        mount_path = Path(__file__).resolve().parent / 'relative-mount'
        updater = ConfigUpdater(allow_no_value=True)
        updater.read_string(
            f"""
[setup]
is_setup_complete = True
setup_mode = manual
storage_mode = nfs
nas_host = server.local
nas_share = media
nas_mount_path = {mount_path}
nas_mount_options = rw
"""
        )

        namer_config = from_config(updater, NamerConfig())

        self.assertTrue(namer_config.is_setup_complete)
        self.assertEqual(namer_config.setup_mode, 'manual')
        self.assertEqual(namer_config.storage_mode, 'nfs')
        self.assertEqual(namer_config.nas_host, 'server.local')
        self.assertEqual(namer_config.nas_share, 'media')
        self.assertEqual(namer_config.nas_mount_path, mount_path.resolve())
        self.assertEqual(namer_config.nas_mount_options, 'rw')

    def test_default_config_tracks_effective_config_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix='namer-config-') as tmpdir:
            config_file = Path(tmpdir) / 'namer.cfg'
            config_file.write_text(
                """
[setup]
is_setup_complete = True

[namer]
porndb_token = abc123

[watchdog]
watch_dir = /tmp/watch
work_dir = /tmp/work
failed_dir = /tmp/failed
dest_dir = /tmp/dest
""",
                encoding='UTF-8',
            )

            namer_config = default_config(config_file)

            self.assertEqual(namer_config.config_file, config_file.resolve())

    def test_proxmox_lxc_handoff_artifact_paths_exist(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent

        self.assertTrue((repo_root / 'contrib' / 'proxmoxved' / 'ct' / 'namer.sh').exists())
        self.assertTrue((repo_root / 'contrib' / 'proxmoxved' / 'install' / 'namer-install.sh').exists())
        self.assertTrue((repo_root / 'docs' / 'proxmox-lxc.md').exists())

        installer_text = (repo_root / 'contrib' / 'proxmoxved' / 'install' / 'namer-install.sh').read_text(encoding='UTF-8')
        ct_text = (repo_root / 'contrib' / 'proxmoxved' / 'ct' / 'namer.sh').read_text(encoding='UTF-8')
        docs_text = (repo_root / 'docs' / 'proxmox-lxc.md').read_text(encoding='UTF-8')

        self.assertIn('source <(curl -fsSL', ct_text)
        self.assertIn('var_tags=', ct_text)
        self.assertIn('build_container', ct_text)
        self.assertIn('description', ct_text)
        self.assertIn('function update_script()', ct_text)
        self.assertIn('https://pypi.org/pypi/namer/json', ct_text)
        self.assertIn('/opt/namer_version.txt', ct_text)
        self.assertIn('updater["watchdog"]["web"].value = "True"', installer_text)
        self.assertIn('source /dev/stdin <<<"$FUNCTIONS_FILE_PATH"', installer_text)
        self.assertIn('setting_up_container', installer_text)
        self.assertIn('cleanup_lxc', installer_text)
        self.assertIn('APP_VERSION_FILE="/opt/namer_version.txt"', installer_text)
        self.assertIn('python3 -m pip install --upgrade "${APP_PIP_SPEC}"', installer_text)
        self.assertIn('import importlib.metadata', installer_text)
        self.assertIn('/var/lib/namer/watch', installer_text)
        self.assertIn('/var/lib/namer/dest', installer_text)
        self.assertIn('APP_PIP_SPEC="${NAMER_PIP_SPEC:-namer}"', installer_text)
        self.assertIn('chown "${APP_USER}:${APP_GROUP}" "${APP_CONFIG}"', installer_text)
        self.assertIn('chmod 0640 "${APP_CONFIG}"', installer_text)
        self.assertIn('web = True', docs_text)
        self.assertIn('/var/lib/namer/watch', docs_text)
        self.assertIn('NAMER_PIP_SPEC', docs_text)
        self.assertIn('PyPI', docs_text)

    def test_proxmoxved_fork_bundle_layout_exists(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        bundle_root = repo_root / 'handoff' / 'proxmoxved-fork'

        self.assertTrue((bundle_root / 'ct' / 'namer.sh').exists())
        self.assertTrue((bundle_root / 'install' / 'namer-install.sh').exists())
        self.assertTrue((bundle_root / 'README.md').exists())

        source_ct = (repo_root / 'contrib' / 'proxmoxved' / 'ct' / 'namer.sh').read_text(encoding='UTF-8')
        source_install = (repo_root / 'contrib' / 'proxmoxved' / 'install' / 'namer-install.sh').read_text(encoding='UTF-8')
        bundle_ct = (bundle_root / 'ct' / 'namer.sh').read_text(encoding='UTF-8')
        bundle_install = (bundle_root / 'install' / 'namer-install.sh').read_text(encoding='UTF-8')
        bundle_readme = (bundle_root / 'README.md').read_text(encoding='UTF-8')

        self.assertEqual(bundle_ct, source_ct)
        self.assertEqual(bundle_install, source_install)
        self.assertIn('community-scripts/ProxmoxVED', bundle_readme)
        self.assertIn('ct/namer.sh', bundle_readme)
        self.assertIn('install/namer-install.sh', bundle_readme)

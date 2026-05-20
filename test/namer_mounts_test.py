"""
Tests setup persistence and NAS mount helpers.
"""

from pathlib import Path
import shutil
import tempfile
import unittest

from loguru import logger

from namer.mounts import (
    build_fstab_line,
    build_nfs_probe_command,
    sanitize_nfs_host,
    sanitize_nfs_share,
)
from namer.setup import SetupPayload, validate_setup_payload, write_setup_config
from test import utils


class UnitTestMountAndSetupServices(unittest.TestCase):
    """
    Always test first.
    """

    def __init__(self, method_name='runTest'):
        super().__init__(method_name)

        if not utils.is_debugging():
            logger.remove()

    def test_validate_setup_payload_requires_host_share_token_and_dirs(self) -> None:
        payload = SetupPayload(
            tpdb_token='',
            nas_host='',
            nas_share='',
            watch_dir='',
            work_dir='',
            failed_dir='',
            dest_dir='',
        )

        errors = validate_setup_payload(payload)

        self.assertEqual(errors['tpdb_token'], 'Required')
        self.assertEqual(errors['nas_host'], 'Required')
        self.assertEqual(errors['nas_share'], 'Required')
        self.assertEqual(errors['watch_dir'], 'Required')
        self.assertEqual(errors['work_dir'], 'Required')
        self.assertEqual(errors['failed_dir'], 'Required')
        self.assertEqual(errors['dest_dir'], 'Required')

    def test_validate_setup_payload_rejects_non_absolute_linux_paths(self) -> None:
        payload = SetupPayload(
            tpdb_token='token-123',
            nas_host='192.168.1.50',
            nas_share='/share/Media',
            watch_dir='relative/watch',
            work_dir='C:\\work',
            failed_dir='/var/lib/namer/failed',
            dest_dir='/mnt/nas/dest',
            nas_mount_path='mnt/nas',
        )

        errors = validate_setup_payload(payload)

        self.assertEqual(errors['watch_dir'], 'Must be an absolute Linux path')
        self.assertEqual(errors['work_dir'], 'Must be an absolute Linux path')
        self.assertEqual(errors['nas_mount_path'], 'Must be an absolute Linux path')

    def test_validate_setup_payload_rejects_host_with_export_path(self) -> None:
        payload = SetupPayload(
            tpdb_token='token-123',
            nas_host='nas.local:/exports',
            nas_share='/share/Media',
            watch_dir='/mnt/nas/watch',
            work_dir='/var/lib/namer/work',
            failed_dir='/var/lib/namer/failed',
            dest_dir='/mnt/nas/dest',
        )

        errors = validate_setup_payload(payload)

        self.assertEqual(errors['nas_host'], 'Must be a hostname or IPv4 address')

    def test_validate_setup_payload_accepts_host_normalized_like_persistence(self) -> None:
        payload = SetupPayload(
            tpdb_token='token-123',
            nas_host=' nas.local:/ ',
            nas_share='/share/Media',
            watch_dir='/mnt/nas/watch',
            work_dir='/var/lib/namer/work',
            failed_dir='/var/lib/namer/failed',
            dest_dir='/mnt/nas/dest',
        )

        errors = validate_setup_payload(payload)

        self.assertNotIn('nas_host', errors)

    def test_write_setup_config_marks_setup_complete(self) -> None:
        config_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(config_dir, ignore_errors=True))
        config_file = config_dir / 'namer.cfg'
        config_file.write_text(
            '[namer]\n'
            'porndb_token =\n'
            'database_path = ./db\n'
            '\n'
            '[watchdog]\n'
            'watch_dir = ./watch\n'
            'work_dir = ./work\n'
            'failed_dir = ./failed\n'
            'dest_dir = ./dest\n',
            encoding='UTF-8',
        )

        payload = SetupPayload(
            tpdb_token='token-123',
            nas_host='192.168.1.50',
            nas_share='/share/Media',
            watch_dir='/mnt/nas/watch',
            work_dir='/var/lib/namer/work',
            failed_dir='/var/lib/namer/failed',
            dest_dir='/mnt/nas/dest',
        )

        write_setup_config(config_file, payload)

        saved = config_file.read_text(encoding='UTF-8')
        self.assertIn('is_setup_complete = True', saved)
        self.assertIn('setup_mode = wizard', saved)
        self.assertIn('storage_mode = nfs', saved)
        self.assertIn('web = True', saved)
        self.assertIn('nas_host = 192.168.1.50', saved)
        self.assertIn('nas_share = /share/Media', saved)
        self.assertIn('porndb_token = token-123', saved)
        self.assertIn('watch_dir = /mnt/nas/watch', saved)
        self.assertIn('database_path = ./db', saved)

    def test_sanitize_nfs_values_and_build_mount_outputs(self) -> None:
        host = sanitize_nfs_host(' nas.local:/ ')
        share = sanitize_nfs_share(' share/Media/ ')
        root_share = sanitize_nfs_share(' / ')

        self.assertEqual(host, 'nas.local')
        self.assertEqual(share, '/share/Media')
        self.assertEqual(root_share, '/')
        self.assertEqual(
            build_nfs_probe_command(host, share, '/mnt/nas'),
            [
                'mount',
                '-t',
                'nfs',
                '-o',
                'ro,nfsvers=3,soft,timeo=5',
                'nas.local:/share/Media',
                '/mnt/nas',
            ],
        )
        self.assertEqual(
            build_fstab_line(host, share, '/mnt/nas', 'defaults,_netdev'),
            'nas.local:/share/Media /mnt/nas nfs defaults,_netdev 0 0',
        )
        self.assertEqual(
            build_fstab_line(host, root_share, '/mnt/nas', 'defaults,_netdev'),
            'nas.local:/ /mnt/nas nfs defaults,_netdev 0 0',
        )


if __name__ == '__main__':
    unittest.main()

"""
Pure helpers for NAS mount configuration.
"""

from pathlib import Path
import subprocess
import tempfile

def sanitize_nfs_host(host: str) -> str:
    """
    Normalize an NFS host without mutating the system.
    """
    return host.strip().rstrip(':/')


def sanitize_nfs_share(share: str) -> str:
    """
    Normalize an NFS share path to a single absolute-style path string.
    """
    cleaned = share.strip()
    if cleaned == '/':
        return '/'

    cleaned = cleaned.rstrip('/')
    if cleaned and not cleaned.startswith('/'):
        cleaned = f'/{cleaned}'
    return cleaned


def build_nfs_probe_command(host: str, share: str, mount_path: str) -> list[str]:
    """
    Build a read-only probe command for an NFS share.
    """
    clean_host = sanitize_nfs_host(host)
    clean_share = sanitize_nfs_share(share)
    return [
        'mount',
        '-t',
        'nfs',
        '-o',
        'ro,nfsvers=3,soft,timeo=5',
        f'{clean_host}:{clean_share}',
        mount_path,
    ]


def build_fstab_line(host: str, share: str, mount_path: str, mount_options: str) -> str:
    """
    Build an /etc/fstab line for an NFS mount.
    """
    clean_host = sanitize_nfs_host(host)
    clean_share = sanitize_nfs_share(share)
    clean_mount_path = mount_path.strip()
    clean_mount_options = mount_options.strip()
    return f'{clean_host}:{clean_share} {clean_mount_path} nfs {clean_mount_options} 0 0'


def probe_nfs_share(host: str, share: str, mount_path: str) -> dict:
    """
    Probe an NFS share using a temporary mountpoint and clean up immediately.
    """
    requested_mount_path = mount_path.strip()
    probe_name = Path(requested_mount_path).name or 'nfs-probe'

    with tempfile.TemporaryDirectory(prefix=f'{probe_name}-') as probe_dir:
        command = build_nfs_probe_command(host, share, probe_dir)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except FileNotFoundError as exc:
            return {
                'ok': False,
                'message': 'NFS probe command is unavailable on this host.',
                'details': {
                    'command': command,
                    'stdout': '',
                    'stderr': str(exc),
                    'returncode': None,
                    'requested_mount_path': requested_mount_path,
                    'probe_mount_path': probe_dir,
                },
            }
        except subprocess.TimeoutExpired as exc:
            return {
                'ok': False,
                'message': 'NFS probe timed out.',
                'details': {
                    'command': command,
                    'stdout': exc.stdout or '',
                    'stderr': exc.stderr or '',
                    'returncode': None,
                    'requested_mount_path': requested_mount_path,
                    'probe_mount_path': probe_dir,
                },
            }

        details = {
            'command': command,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'requested_mount_path': requested_mount_path,
            'probe_mount_path': probe_dir,
        }
        if result.returncode != 0:
            return {
                'ok': False,
                'message': 'NFS probe failed.',
                'details': details,
            }

        try:
            cleanup = subprocess.run(
                ['umount', probe_dir],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except FileNotFoundError as exc:
            details['cleanup'] = {
                'command': ['umount', probe_dir],
                'stdout': '',
                'stderr': str(exc),
                'returncode': None,
            }
            return {
                'ok': False,
                'message': 'NFS probe mounted successfully but cleanup is unavailable on this host.',
                'details': details,
            }
        except subprocess.TimeoutExpired as exc:
            details['cleanup'] = {
                'command': ['umount', probe_dir],
                'stdout': exc.stdout or '',
                'stderr': exc.stderr or '',
                'returncode': None,
            }
            return {
                'ok': False,
                'message': 'NFS probe mounted successfully but cleanup timed out.',
                'details': details,
            }
        details['cleanup'] = {
            'command': ['umount', probe_dir],
            'stdout': cleanup.stdout,
            'stderr': cleanup.stderr,
            'returncode': cleanup.returncode,
        }
        if cleanup.returncode != 0:
            return {
                'ok': False,
                'message': 'NFS probe mounted successfully but cleanup failed.',
                'details': details,
            }

        return {
            'ok': True,
            'message': 'NFS probe succeeded.',
            'details': details,
        }

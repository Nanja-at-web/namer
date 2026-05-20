"""
Setup validation and configuration persistence helpers.
"""

from dataclasses import dataclass
from ipaddress import AddressValueError, IPv4Address
from pathlib import Path
import re
from typing import Any, Dict

from configupdater import ConfigUpdater

from namer.configuration import NamerConfig
from namer.configuration_utils import resource_file_to_str
from namer.mounts import sanitize_nfs_host, sanitize_nfs_share


@dataclass
class SetupPayload:
    tpdb_token: str
    nas_host: str
    nas_share: str
    watch_dir: str
    work_dir: str
    failed_dir: str
    dest_dir: str
    storage_mode: str = 'nfs'
    nas_mount_path: str = '/mnt/nas'
    nas_mount_options: str = 'defaults,_netdev'


def _is_absolute_linux_path(value: str) -> bool:
    cleaned = value.strip()
    return bool(cleaned) and cleaned.startswith('/') and '\\' not in cleaned


def _looks_like_host_plus_export(value: str) -> bool:
    cleaned = value.strip()
    if ':/' not in cleaned:
        return False

    _, suffix = cleaned.split(':/', 1)
    return bool(suffix.strip('/'))


def _is_valid_hostname_or_ipv4(value: str) -> bool:
    if not value:
        return False

    try:
        IPv4Address(value)
        return True
    except AddressValueError:
        pass

    return bool(
        re.fullmatch(
            r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*',
            value,
        ),
    )


def _normalized_payload(payload: SetupPayload) -> SetupPayload:
    return SetupPayload(
        tpdb_token=payload.tpdb_token.strip(),
        nas_host=sanitize_nfs_host(payload.nas_host),
        nas_share=sanitize_nfs_share(payload.nas_share),
        watch_dir=payload.watch_dir.strip(),
        work_dir=payload.work_dir.strip(),
        failed_dir=payload.failed_dir.strip(),
        dest_dir=payload.dest_dir.strip(),
        storage_mode=payload.storage_mode.strip() or 'nfs',
        nas_mount_path=payload.nas_mount_path.strip() or '/mnt/nas',
        nas_mount_options=payload.nas_mount_options.strip() or 'defaults,_netdev',
    )


def validate_setup_payload(payload: SetupPayload) -> Dict[str, str]:
    """
    Validate setup payload contents without mutating config.
    """
    raw_nas_host = payload.nas_host.strip()
    normalized = _normalized_payload(payload)
    errors: Dict[str, str] = {}

    required_values = {
        'tpdb_token': normalized.tpdb_token,
        'nas_host': normalized.nas_host,
        'nas_share': normalized.nas_share,
        'watch_dir': normalized.watch_dir,
        'work_dir': normalized.work_dir,
        'failed_dir': normalized.failed_dir,
        'dest_dir': normalized.dest_dir,
    }
    for field, value in required_values.items():
        if not value:
            errors[field] = 'Required'

    if raw_nas_host and (
        _looks_like_host_plus_export(raw_nas_host)
        or not _is_valid_hostname_or_ipv4(normalized.nas_host)
    ):
        errors['nas_host'] = 'Must be a hostname or IPv4 address'

    if normalized.storage_mode != 'nfs':
        errors['storage_mode'] = 'Unsupported storage mode'

    for field in ('watch_dir', 'work_dir', 'failed_dir', 'dest_dir', 'nas_mount_path'):
        value = getattr(normalized, field)
        if value and not _is_absolute_linux_path(value):
            errors[field] = 'Must be an absolute Linux path'

    return errors


def validate_nfs_probe_payload(payload: SetupPayload) -> Dict[str, str]:
    """
    Validate only the fields required to probe NFS connectivity.
    """
    normalized = _normalized_payload(payload)
    errors: Dict[str, str] = {}

    if not normalized.nas_host:
        errors['nas_host'] = 'Required'
    elif not _is_valid_hostname_or_ipv4(normalized.nas_host):
        errors['nas_host'] = 'Must be a hostname or IPv4 address'

    if not normalized.nas_share:
        errors['nas_share'] = 'Required'

    if not normalized.nas_mount_path:
        errors['nas_mount_path'] = 'Required'
    elif not _is_absolute_linux_path(normalized.nas_mount_path):
        errors['nas_mount_path'] = 'Must be an absolute Linux path'

    return errors


def setup_payload_from_request(data: Dict[str, Any]) -> SetupPayload:
    """
    Build a setup payload from camelCase or snake_case API request data.
    """
    payload = data or {}

    def read_value(*keys: str, default: str = '') -> str:
        for key in keys:
            value = payload.get(key)
            if value is None:
                continue
            return str(value)
        return default

    return SetupPayload(
        tpdb_token=read_value('tpdbToken', 'tpdb_token'),
        nas_host=read_value('nasHost', 'nas_host'),
        nas_share=read_value('nasShare', 'nas_share'),
        watch_dir=read_value('watchDir', 'watch_dir'),
        work_dir=read_value('workDir', 'work_dir'),
        failed_dir=read_value('failedDir', 'failed_dir'),
        dest_dir=read_value('destDir', 'dest_dir'),
        storage_mode=read_value('storageMode', 'storage_mode', default='nfs'),
        nas_mount_path=read_value('nasMountPath', 'nas_mount_path', default='/mnt/nas'),
        nas_mount_options=read_value('nasMountOptions', 'nas_mount_options', default='defaults,_netdev'),
    )


def _merge_missing_defaults(target: ConfigUpdater, defaults: ConfigUpdater) -> None:
    for section_name in defaults.sections():
        if not target.has_section(section_name):
            target.add_section(section_name)

        target_section = target[section_name]
        default_section = defaults[section_name]
        for option_name in default_section.options():
            if not target_section.has_option(option_name):
                default_option = default_section[option_name]
                target_section.add_option(
                    target_section.create_option(option_name, default_option.value),
                )


def _set_config_value(updater: ConfigUpdater, section: str, option: str, value: str) -> None:
    updater[section][option].value = value


def write_setup_config(config_file: Path, payload: SetupPayload) -> None:
    """
    Persist validated setup values into the namer config file.
    """
    normalized = _normalized_payload(payload)
    errors = validate_setup_payload(normalized)
    if errors:
        raise ValueError(f'Invalid setup payload: {errors}')

    defaults = ConfigUpdater(allow_no_value=True)
    defaults.read_string(resource_file_to_str('namer', 'namer.cfg.default'))

    updater = ConfigUpdater(allow_no_value=True)
    if config_file.is_file():
        updater.read(config_file, encoding='UTF-8')
    _merge_missing_defaults(updater, defaults)
    _set_config_value(updater, 'setup', 'is_setup_complete', 'True')
    _set_config_value(updater, 'setup', 'setup_mode', 'wizard')
    _set_config_value(updater, 'setup', 'storage_mode', normalized.storage_mode)
    _set_config_value(updater, 'setup', 'nas_host', normalized.nas_host)
    _set_config_value(updater, 'setup', 'nas_share', normalized.nas_share)
    _set_config_value(updater, 'setup', 'nas_mount_path', normalized.nas_mount_path)
    _set_config_value(updater, 'setup', 'nas_mount_options', normalized.nas_mount_options)
    _set_config_value(updater, 'namer', 'porndb_token', normalized.tpdb_token)
    _set_config_value(updater, 'watchdog', 'watch_dir', normalized.watch_dir)
    _set_config_value(updater, 'watchdog', 'work_dir', normalized.work_dir)
    _set_config_value(updater, 'watchdog', 'failed_dir', normalized.failed_dir)
    _set_config_value(updater, 'watchdog', 'dest_dir', normalized.dest_dir)
    _set_config_value(updater, 'watchdog', 'web', 'True')

    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(str(updater), encoding='UTF-8')


def apply_setup_payload(config: NamerConfig, payload: SetupPayload) -> None:
    """
    Update the in-memory config after a successful setup save.
    """
    normalized = _normalized_payload(payload)
    config.is_setup_complete = True
    config.setup_mode = 'wizard'
    config.storage_mode = normalized.storage_mode
    config.nas_host = normalized.nas_host
    config.nas_share = normalized.nas_share
    config.nas_mount_path = Path(normalized.nas_mount_path)
    config.nas_mount_options = normalized.nas_mount_options
    config.porndb_token = normalized.tpdb_token
    config.watch_dir = Path(normalized.watch_dir)
    config.work_dir = Path(normalized.work_dir)
    config.failed_dir = Path(normalized.failed_dir)
    config.dest_dir = Path(normalized.dest_dir)
    config.web = True

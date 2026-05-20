from queue import Queue

import pytest

import namer.web.routes.api as api_routes
from namer.web.server import NamerWebServer
from test.utils import sample_config


@pytest.fixture
def config():
    return sample_config()


@pytest.fixture
def client(config):
    server = NamerWebServer(config, Queue())
    app = server.get_app()
    app.testing = True

    with app.test_client() as test_client:
        yield test_client


def test_failed_route_redirects_to_setup_when_config_incomplete(client, config):
    config.is_setup_complete = False

    response = client.get('/failed')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/setup')


def test_index_route_redirects_to_setup_when_config_incomplete(client, config):
    config.is_setup_complete = False

    response = client.get('/')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/setup')


def test_queue_route_redirects_to_setup_when_config_incomplete(client, config):
    config.is_setup_complete = False

    response = client.get('/queue')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/setup')


def test_settings_route_redirects_to_setup_when_config_incomplete(client, config):
    config.is_setup_complete = False

    response = client.get('/settings')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/setup')


def test_setup_page_renders_when_config_incomplete(client, config):
    config.is_setup_complete = False

    response = client.get('/setup')

    assert response.status_code == 200
    assert b'Namer Setup Wizard' in response.data


def test_setup_page_contains_nas_and_token_fields(client, config):
    config.is_setup_complete = False

    response = client.get('/setup')

    body = response.data.decode()

    assert 'name="nasHost"' in body
    assert 'name="nasShare"' in body
    assert 'name="tpdbToken"' in body
    assert 'name="watchDir"' in body


def test_setup_page_uses_runtime_defaults_and_webroot(client, config):
    config.is_setup_complete = False
    config.web_root = '/namer'
    config.storage_mode = 'nfs'
    config.nas_host = '192.168.1.50'
    config.nas_share = '/share/Media'
    config.nas_mount_path = '/mnt/nas'
    config.nas_mount_options = 'defaults,_netdev'
    config.watch_dir = '/mnt/nas/watch'
    config.work_dir = '/var/lib/namer/work'
    config.failed_dir = '/var/lib/namer/failed'
    config.dest_dir = '/mnt/nas/dest'

    response = client.get('/setup')

    body = response.data.decode()

    assert 'data-api-url="/namer/api/v1/setup/save"' in body
    assert 'value="192.168.1.50"' in body
    assert 'value="/share/Media"' in body
    assert 'value="/mnt/nas/dest"' in body


def test_healthcheck_is_not_redirected_when_config_incomplete(client, config):
    config.is_setup_complete = False

    response = client.get('/api/healthcheck')

    assert response.status_code == 200
    assert response.json == {'status': 'OK'}


def test_server_normalizes_webroot_for_blueprints(config):
    config.is_setup_complete = True
    config.web_root = '/namer/'
    server = NamerWebServer(config, Queue())
    app = server.get_app()

    routes = {rule.rule for rule in app.url_map.iter_rules()}

    assert '/namer/failed' in routes
    assert '/namer/setup' in routes
    assert '/namer/api/healthcheck' in routes

    with app.test_client() as test_client:
        response = test_client.get('/namer/')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/namer/failed')


def test_setup_validate_returns_field_errors(client, config):
    config.is_setup_complete = False

    response = client.post('/api/v1/setup/validate', json={'tpdbToken': ''})

    assert response.status_code == 400
    payload = response.get_json()
    assert payload['ok'] is False
    assert payload['errors']['tpdb_token'] == 'Required'
    assert payload['errors']['nas_host'] == 'Required'


def test_setup_save_marks_wizard_complete(client, config, tmp_path):
    config.is_setup_complete = False
    config.config_file = tmp_path / 'namer.cfg'
    config.config_file.write_text(
        '[namer]\nporndb_token =\n[watchdog]\nwatch_dir = ./watch\nwork_dir = ./work\nfailed_dir = ./failed\ndest_dir = ./dest\n',
        encoding='UTF-8',
    )

    response = client.post(
        '/api/v1/setup/save',
        json={
            'tpdbToken': 'abc123',
            'nasHost': '192.168.1.50',
            'nasShare': '/share/Media',
            'watchDir': '/mnt/nas/watch',
            'workDir': '/var/lib/namer/work',
            'failedDir': '/var/lib/namer/failed',
            'destDir': '/mnt/nas/dest',
        },
    )

    assert response.status_code == 200
    assert response.get_json()['ok'] is True
    assert 'is_setup_complete = True' in config.config_file.read_text(encoding='UTF-8')


def test_setup_test_nfs_probes_without_persisting(client, config, tmp_path, monkeypatch):
    config.is_setup_complete = False
    config.config_file = tmp_path / 'namer.cfg'
    config.config_file.write_text(
        '[namer]\nporndb_token =\n[watchdog]\nwatch_dir = ./watch\nwork_dir = ./work\nfailed_dir = ./failed\ndest_dir = ./dest\n',
        encoding='UTF-8',
    )

    def fake_probe_nfs_share(host, share, mount_path):
        assert host == '192.168.1.50'
        assert share == '/share/Media'
        assert mount_path == '/mnt/nas'
        return {
            'ok': True,
            'message': 'Probe succeeded',
            'details': {
                'command': ['mount', '-t', 'nfs'],
                'stdout': '',
                'stderr': '',
                'returncode': 0,
            },
        }

    monkeypatch.setattr(api_routes, 'probe_nfs_share', fake_probe_nfs_share)

    response = client.post(
        '/api/v1/setup/test_nfs',
        json={
            'nasHost': '192.168.1.50',
            'nasShare': '/share/Media',
            'nasMountPath': '/mnt/nas',
        },
    )

    assert response.status_code == 200
    assert response.get_json()['ok'] is True
    assert 'is_setup_complete = True' not in config.config_file.read_text(encoding='UTF-8')

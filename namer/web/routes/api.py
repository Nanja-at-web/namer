"""
Defines the api routes of a Flask webserver for namer.
"""

from pathlib import Path
from queue import Queue

from flask import Blueprint, jsonify, render_template, request
from flask.wrappers import Response

from namer.command import make_command_relative_to, move_command_files
from namer.configuration import NamerConfig
from namer.mounts import probe_nfs_share
from namer.setup import apply_setup_payload, setup_payload_from_request, validate_nfs_probe_payload, validate_setup_payload, write_setup_config
from namer.web.actions import delete_file, get_failed_files, get_phash_results, get_queue_size, get_queued_files, get_search_results, human_format, read_failed_log_file


def get_routes(config: NamerConfig, command_queue: Queue) -> Blueprint:
    """
    Builds a blueprint for flask with passed in context, the NamerConfig.
    """
    blueprint = Blueprint('api', __name__, url_prefix='/api')

    def failed_redirect() -> str:
        web_root = (config.web_root or '').rstrip('/')
        return f'{web_root}/failed' if web_root else '/failed'

    @blueprint.route('/v1/render', methods=['POST'])
    def render() -> Response:
        data = request.json

        res = False
        if data:
            template: str = data.get('template')
            client_data = data.get('data')

            active_page: str = data.get('url')
            if config.web_root and config.web_root != '':
                active_page = active_page.replace(config.web_root, '') if active_page.startswith(config.web_root) else active_page
            active_page = active_page.lstrip('/')

            template_file = f'render/{template}.html'
            response = render_template(template_file, data=client_data, config=config, active_page=active_page)

            res = {
                'response': response,
            }

        return jsonify(res)

    @blueprint.route('/v1/get_files', methods=['POST'])
    def get_files() -> Response:
        data = get_failed_files(config)
        return jsonify(data)

    @blueprint.route('/v1/get_queued', methods=['POST'])
    def get_queued() -> Response:
        data = get_queued_files(command_queue, config)
        return jsonify(data)

    @blueprint.route('/v1/get_search', methods=['POST'])
    def get_search() -> Response:
        data = request.json

        res = False
        if data:
            page = data['page'] if 'page' in data else 1
            res = get_search_results(data['query'], data['type'], data['file'], config, page=page)

        return jsonify(res)

    @blueprint.route('/v1/get_phash', methods=['POST'])
    def get_phash() -> Response:
        data = request.json

        res = False
        if data:
            res = get_phash_results(data['file'], data['type'], config)

        return jsonify(res)

    @blueprint.route('/v1/get_queue', methods=['POST'])
    def get_queue() -> Response:
        res = get_queue_size(command_queue)
        res = human_format(res)

        return jsonify(res)

    @blueprint.route('/v1/rename', methods=['POST'])
    def rename() -> Response:
        data = request.json

        res = False
        if data:
            res = False
            movie = config.failed_dir / Path(data['file'])
            command = make_command_relative_to(movie, config.failed_dir, config=config, is_auto=False)
            moved_command = move_command_files(command, config.work_dir, is_auto=False)
            if moved_command:
                moved_command.tpdb_id = data['scene_id']
                command_queue.put(moved_command)  # Todo pass selection

        return jsonify(res)

    @blueprint.route('/v1/delete', methods=['POST'])
    def delete() -> Response:
        data = request.json

        res = False
        if data:
            res = delete_file(data['file'], config)

        return jsonify(res)

    @blueprint.route('/v1/read_failed_log', methods=['POST'])
    def read_failed_log() -> Response:
        data = request.json

        res = False
        if data:
            # fmt: off
            res = {
                'file': data['file'],
                'data': read_failed_log_file(data['file'], config)
            }

        return jsonify(res)

    @blueprint.route('/v1/setup/validate', methods=['POST'])
    def setup_validate() -> Response:
        payload = setup_payload_from_request(request.json or {})
        errors = validate_setup_payload(payload)

        response = jsonify(
            {
                'ok': len(errors) == 0,
                'errors': errors,
            },
        )
        if errors:
            response.status_code = 400
        return response

    @blueprint.route('/v1/setup/save', methods=['POST'])
    def setup_save() -> Response:
        payload = setup_payload_from_request(request.json or {})
        errors = validate_setup_payload(payload)
        if errors:
            response = jsonify(
                {
                    'ok': False,
                    'errors': errors,
                    'message': 'Setup payload is invalid.',
                },
            )
            response.status_code = 400
            return response

        write_setup_config(config.config_file, payload)
        apply_setup_payload(config, payload)
        return jsonify(
            {
                'ok': True,
                'redirect': failed_redirect(),
            },
        )

    @blueprint.route('/v1/setup/test_nfs', methods=['POST'])
    def setup_test_nfs() -> Response:
        payload = setup_payload_from_request(request.json or {})
        errors = validate_nfs_probe_payload(payload)
        if errors:
            response = jsonify(
                {
                    'ok': False,
                    'errors': errors,
                    'message': 'NFS probe payload is invalid.',
                },
            )
            response.status_code = 400
            return response

        result = probe_nfs_share(payload.nas_host, payload.nas_share, payload.nas_mount_path)
        response = jsonify(result)
        if not result.get('ok'):
            response.status_code = 502
        return response

    @blueprint.route('/healthcheck', methods=['GET'])
    def healthcheck() -> Response:
        # fmt: off
        res = {
            'status': 'OK',
        }

        return jsonify(res)

    return blueprint

"""
Defines the web routes of a Flask webserver for namer.
"""

from queue import Queue

from flask import Blueprint, redirect, render_template, request, url_for
from flask.wrappers import Response

from namer.configuration import NamerConfig
from namer.metadataapi import get_user_info
from namer.web.actions import get_failed_files, get_queued_files


def require_completed_setup(config: NamerConfig) -> Response | None:
    if not config.is_setup_complete:
        return redirect(url_for('web.setup'), code=302)  # type: ignore

    return None


def get_routes(config: NamerConfig, command_queue: Queue) -> Blueprint:
    """
    Builds a blueprint for flask with passed in context, the NamerConfig.
    """
    blueprint = Blueprint('web', __name__)

    @blueprint.route('/')
    def index() -> Response:
        redirect_response = require_completed_setup(config)
        if redirect_response:
            return redirect_response

        return redirect(url_for('web.failed'), code=302)  # type: ignore

    @blueprint.route('/setup')
    def setup() -> str:
        theme = request.cookies.get('theme', 'auto')
        return render_template(
            'pages/setup.html',
            config=config,
            theme=theme,
            user=None,
            active_page='setup',
            setup_defaults={
                'storageMode': config.storage_mode,
                'nasHost': config.nas_host,
                'nasShare': config.nas_share,
                'nasMountPath': config.nas_mount_path,
                'nasMountOptions': config.nas_mount_options,
                'watchDir': str(config.watch_dir),
                'workDir': str(config.work_dir),
                'failedDir': str(config.failed_dir),
                'destDir': str(config.dest_dir),
            },
        )

    @blueprint.route('/failed')
    def failed() -> Response | str:
        """
        Displays all failed to name files.
        """
        redirect_response = require_completed_setup(config)
        if redirect_response:
            return redirect_response

        data = get_failed_files(config)
        theme = request.cookies.get('theme', 'auto')
        user = get_user_info(config)

        return render_template('pages/failed.html', data=data, config=config, theme=theme, user=user)

    @blueprint.route('/queue')
    def queue() -> Response | str:
        """
        Displays all queued files.
        """
        redirect_response = require_completed_setup(config)
        if redirect_response:
            return redirect_response

        data = get_queued_files(command_queue, config)
        theme = request.cookies.get('theme', 'auto')
        user = get_user_info(config)

        return render_template('pages/queue.html', data=data, config=config, theme=theme, user=user)

    @blueprint.route('/settings')
    def settings() -> Response | str:
        """
        Displays namer settings.
        """
        redirect_response = require_completed_setup(config)
        if redirect_response:
            return redirect_response

        theme = request.cookies.get('theme', 'auto')
        user = get_user_info(config)

        return render_template('pages/settings.html', config=config, theme=theme, user=user)

    return blueprint

"""Define Mesito as Flask application."""

# pylint: disable=invalid-name
# pylint: disable=no-member
from typing import Any

import flask
import sqlalchemy.orm

import mesito.route


def _v1_api_blueprint(
        session_factory: sqlalchemy.orm.scoped_session) -> flask.Blueprint:
    """
    Produce v1 API blueprint.

    :param session_factory: SQLAlchemy session factory
    :return: flask application
    """
    blueprint = flask.Blueprint(name='api_v1', import_name=__name__)

    blueprint.route(
        '/put_machine', methods=['POST'], endpoint='put_machine')(
            lambda: mesito.route.put_machine(session_factory=session_factory))

    blueprint.route(
        '/machines', methods=['POST'], endpoint='machines'
    )(lambda: mesito.route.serve_machines(session_factory=session_factory))

    blueprint.route(
        '/put_machine_state', methods=['POST'], endpoint='put_machine_state'
    )(lambda: mesito.route.put_machine_state(session_factory=session_factory))

    return blueprint


def _static_blueprint() -> flask.Blueprint:
    """
    Produce route blueprint for serving static files.

    :return: generated blueprint
    """
    blueprint = flask.Blueprint('static', __name__)

    blueprint.route('/', endpoint='serve_index')(mesito.route.serve_index)

    blueprint.route(
        '/<path:path>', endpoint='serve_static')(mesito.route.serve_static)

    return blueprint


def produce(session_factory: sqlalchemy.orm.scoped_session) -> flask.Flask:
    """
    Produce our flask application.

    :param session_factory: SQLAlchemy session factory
    :return: flask application
    """
    app = flask.Flask(__name__)

    v1_api = _v1_api_blueprint(session_factory=session_factory)
    app.register_blueprint(v1_api, url_prefix='/api/v1')

    static = _static_blueprint()
    app.register_blueprint(static)

    def cleanup(resp_or_exc: Any) -> Any:  # pylint: disable=unused-argument, unused-variable
        """Release resources acquired in an app context."""
        session_factory.remove()

    app.teardown_appcontext(cleanup)

    return app

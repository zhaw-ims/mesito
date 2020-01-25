"""Define Mesito as Flask application."""

# pylint: disable=invalid-name
# pylint: disable=no-member
from typing import Any, Tuple

import flask
import flask_cors
import flask_socketio
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
        '/machines', methods=['POST'], endpoint='post_machine')(
            lambda: mesito.route.post_machine(session_factory=session_factory))

    blueprint.route(
        '/machines/<int:id>', methods=['PATCH'], endpoint='patch_machine')(
            lambda id: mesito.route.patch_machine(
                session_factory=session_factory, id=id))

    blueprint.route(
        '/machines/<int:id>', methods=['DELETE'], endpoint='delete_machine')(
            lambda id: mesito.route.delete_machine(
                session_factory=session_factory, id=id))

    blueprint.route(
        '/machines', methods=['GET'], endpoint='get_machines')(
            lambda: mesito.route.get_machines(session_factory=session_factory))

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


# yapf: disable
def produce(
        session_factory: sqlalchemy.orm.scoped_session,
        cors_allowed_all_origins: bool
) -> Tuple[flask.Flask, flask_socketio.SocketIO]:  # yapf: enable
    """
    Produce our flask application.

    :param session_factory: SQLAlchemy session factory
    :param cors_allowed_origins:
        if set, changes the CORS allowed origins of the app to everybody
    :return: flask application
    """
    app = flask.Flask(__name__)

    v1_api = _v1_api_blueprint(session_factory=session_factory)
    app.register_blueprint(v1_api, url_prefix='/api/v1')

    static = _static_blueprint()
    app.register_blueprint(static)

    if cors_allowed_all_origins:
        flask_cors.CORS(app)
        socketio = flask_socketio.SocketIO(app=app, cors_allowed_origins="*")
    else:
        socketio = flask_socketio.SocketIO(app=app)

    def cleanup(
            resp_or_exc: Any) -> Any:  # pylint: disable=unused-argument, unused-variable
        """Release resources acquired in an app context."""
        session_factory.remove()

    app.teardown_appcontext(cleanup)

    return app, socketio

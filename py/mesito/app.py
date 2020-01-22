"""Define Mesito as Flask application."""

# pylint: disable=invalid-name
# pylint: disable=no-member
from typing import Union, Tuple, Any

import flask
import gevent.pywsgi  # pylint: disable=unused-import
import sqlalchemy.orm  # pylint: disable=unused-import
import flask_socketio
import flask_cors

import mesito.front.error
import mesito.front.valid
import mesito.model
import mesito.operation


def broadcast_put_machine(data: mesito.front.valid.MachinePut)->None:
    """Broadcast the machine change to all the observers."""

def put_machine(session_factory: sqlalchemy.orm.scoped_session) -> Any:  # pylint: disable=unused-variable
    """Upsert a machine."""
    session = session_factory()

    data, local_err = mesito.front.valid.machine_put(data=flask.request.json)

    if local_err is not None:
        return flask.jsonify(local_err), 400

    assert data is not None

    machine_id, global_err = mesito.operation.put_machine(
        session=session, data=data)

    if global_err is not None:
        return flask.jsonify(global_err), 400

    # Set the ID in case the machine is new, so that the observers can
    # observe the full change of the database.
    data["id"] = machine_id

    flask_socketio.emit("put_machine", data, broadcast=True)

    return flask.jsonify(machine_id), 200


def serve_machines(session_factory: sqlalchemy.orm.scoped_session) -> Any:  # pylint: disable=unused-variable
    """Serve the list of all machines."""
    session = session_factory()

    machines = mesito.operation.get_machines(session=session)

    return flask.jsonify(machines)


def put_machine_state(session_factory: sqlalchemy.orm.scoped_session) -> Any:  # pylint: disable=unused-variable
    data, local_err = mesito.front.valid.machine_state_put(
        data=flask.request.json)

    if local_err is not None:
        return flask.jsonify(local_err), 400

    assert data is not None

    session = session_factory()

    machine_state_id, global_err = mesito.operation.put_machine_state(
        session=session, data=data)

    if global_err is not None:
        return flask.jsonify(global_err), 400

    assert machine_state_id is not None

    return flask.jsonify(machine_state_id)


def serve_index() -> Any:  # pylint: disable=unused-variable
    """Serve the index page."""
    return flask.send_from_directory(directory='static', filename='index.html')


def serve_static(path: str) -> Any:  # pylint: disable=unused-variable
    """Serve static files."""
    return flask.send_from_directory(directory='static', filename=path)


def produce(session_factory: sqlalchemy.orm.scoped_session) -> flask.Flask:
    """
    Produce our flask application.

    Make sure you register server blueprint if you want to add control
    capabilities with ``register_server``.

    :param server: WSGI server
    :param session_factory: SQLAlchemy session factory
    :return: flask application
    """
    app = flask.Flask(__name__)
    flask_cors.CORS(app, resources={r"/*": {"origins": "*"}})

    socketio = flask_socketio.SocketIO(app=app, cors_allowed_origins="*")

    app.route(
        '/api/put_machine', methods=['POST'], endpoint='put_machine')(
            lambda: put_machine(session_factory=session_factory))

    app.route(
        '/api/machines', methods=['POST'], endpoint='machines')(
            lambda: serve_machines(session_factory=session_factory))

    app.route(
        '/api/put_machine_state',
        methods=['POST'],
        endpoint='put_machine_state')(
            lambda: put_machine_state(session_factory=session_factory))

    app.route('/',
              methods=['GET'],
              endpoint='serve_index')(serve_index)

    app.route('/<path:path>', endpoint='serve_static')(serve_static)

    @socketio.on('machine_change')
    def handle_message(message):
        emit('machine_change', message , broadcast=True)

    @app.teardown_appcontext
    def cleanup(resp_or_exc: Any) -> Any:  # pylint: disable=unused-argument, unused-variable
        """Release resources acquired in an app context."""
        session_factory.remove()

    return socketio, app


def register_server(server: gevent.pywsgi.WSGIServer, app: flask.Flask) -> None:
    """
    Register WSGI server with the app and add control routes.

    :param server: wsgi server to be controlled
    :param app: flask application
    :return:
    """

    # (Pacify pydocstyle)
    @app.route('/api/shutdown', methods=['POST'], endpoint='shutdown')
    def shutdown() -> Union[str, Tuple[str, int]]:  # pylint: disable=unused-variable
        """Instruct the server to shut down."""
        app.logger.info("Received a shut down request.")
        server.stop()
        return "Shutting down...\n"

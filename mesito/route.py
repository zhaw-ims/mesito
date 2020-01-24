"""Handle application URL routes."""
from typing import Any

import flask
import flask_socketio
import sqlalchemy.orm

import mesito.front.valid
import mesito.operation


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

    assert machine_id is not None, \
        "Expected machine ID to be set on successful operation"

    emission = mesito.front.valid.machine_put_emit(data=data, id=machine_id)

    flask_socketio.emit("put_machine", emission, broadcast=True, namespace="/")

    return flask.jsonify(machine_id), 200


def serve_machines(session_factory: sqlalchemy.orm.scoped_session) -> Any:  # pylint: disable=unused-variable
    """Serve the list of all machines."""
    session = session_factory()

    machines = mesito.operation.get_machines(session=session)

    return flask.jsonify(machines)


def put_machine_state(session_factory: sqlalchemy.orm.scoped_session) -> Any:  # pylint: disable=unused-variable
    """Upsert the state of the given machine."""
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

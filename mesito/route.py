"""Handle application URL routes."""
from typing import Any

import flask
import flask_socketio
import sqlalchemy.orm

import mesito.front.valid
import mesito.front.out
import mesito.operation


def post_machine(session_factory: sqlalchemy.orm.scoped_session) -> Any:  # pylint: disable=unused-variable
    """Post a new machine."""
    session = session_factory()

    data, local_err = mesito.front.valid.machine_post(data=flask.request.json)

    if local_err is not None:
        return flask.jsonify(local_err), 400

    assert data is not None

    machine_id, version = mesito.operation.create_machine(
        session=session, data=data)

    emission = mesito.front.out.machine_put_emit(
        id=machine_id, name=data["name"], version=version)

    flask_socketio.emit("put_machine", emission, broadcast=True, namespace="/")

    return flask.jsonify(machine_id), 200


# yapf: disable
def patch_machine(
        session_factory: sqlalchemy.orm.scoped_session,
        id: int  # pylint: disable=redefined-builtin
) -> Any:  # yapf: enable
    """Patch a machine."""
    session = session_factory()

    data, local_err = mesito.front.valid.machine_patch(data=flask.request.json)

    if local_err is not None:
        return flask.jsonify(local_err), 400

    assert data is not None

    version, global_err = mesito.operation.patch_machine(
        session=session, id=id, data=data)

    if global_err is not None:
        return flask.jsonify(global_err), 400

    assert version is not None

    emission = mesito.front.out.machine_patch_emit(
        data=data, id=id, version=version)

    flask_socketio.emit("put_machine", emission, broadcast=True, namespace="/")

    return flask.jsonify(version), 200

# yapf: disable
def delete_machine(
        session_factory: sqlalchemy.orm.scoped_session,
        id: int  # pylint: disable=redefined-builtin
) -> Any:  # yapf: enable
    """Delete a machine."""
    session = session_factory()

    mesito.operation.delete_machine(session=session, id=id)

    emission = mesito.front.out.machine_delete_emit(id=id)
    flask_socketio.emit(
        "delete_machine", emission, broadcast=True, namespace="/")

    return '', 200


def get_machines(session_factory: sqlalchemy.orm.scoped_session) -> Any:  # pylint: disable=unused-variable
    """Serve the list of all machines."""
    session = session_factory()

    machines = mesito.operation.machines(session=session)

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

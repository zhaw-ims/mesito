#!/usr/bin/env python3

# pylint: disable=missing-docstring
import contextlib
import unittest
from typing import Any, Iterator, Tuple

import flask.testing
import flask.wrappers
import flask_socketio
import sqlalchemy
import sqlalchemy.orm

import mesito.app
import mesito.model
import mesito.operation


# yapf: disable
@contextlib.contextmanager
def client_fixture(
) -> Iterator[  # type: ignore
    Tuple[
        flask.testing.FlaskClient,
        flask_socketio.SocketIOTestClient]]:
    # yapf: enable
    """Create and tear down a temporary client."""
    # See https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#connect-strings
    database_url = 'sqlite://'

    engine = sqlalchemy.create_engine(database_url)

    mesito.model.Base.metadata.create_all(engine)

    session_factory = sqlalchemy.orm.scoped_session(
        sqlalchemy.orm.sessionmaker(bind=engine))

    app, socketio = mesito.app.produce(
        session_factory=session_factory, cors_allowed_all_origins=False)

    with contextlib.ExitStack() as exit_stack:
        client = app.test_client()
        exit_stack.push(client)

        websocket = flask_socketio.SocketIOTestClient(
            app=app, socketio=socketio, flask_test_client=client)
        websocket.connect()

        exit_stack.callback(websocket.disconnect)

        yield client, websocket


def assert_response_type(resp: Any) -> flask.wrappers.Response:
    """Assert that the type of the response is as expected."""
    assert isinstance(resp, flask.wrappers.Response)
    return resp


class TestStatic(unittest.TestCase):
    def test_root(self) -> None:
        with client_fixture() as (client, _):
            resp = assert_response_type(client.get('/'))

            with contextlib.closing(resp):
                self.assertEqual(200, resp.status_code)

    def test_index_html(self) -> None:
        with client_fixture() as (client, _):
            resp = assert_response_type(client.get('/index.html'))

            with contextlib.closing(resp):
                self.assertEqual(200, resp.status_code)


class TestGetMachines(unittest.TestCase):
    def test_on_empty(self) -> None:
        with client_fixture() as (client, _):
            resp = assert_response_type(client.get('/api/v1/machines'))
            self.assertEqual(200, resp.status_code)

            self.assertListEqual([], resp.json)


class TestPostMachine(unittest.TestCase):
    def test_fails_with_nonjson(self) -> None:
        with client_fixture() as (client, websocket):
            resp = assert_response_type(
                client.post('/api/v1/machines', data='so not json'))
            self.assertEqual(400, resp.status_code)
            self.assertEqual({
                'what': 'SchemaViolation',
                'why': 'data must be object'
            }, resp.json)

            self.assertListEqual([], websocket.get_received())

    def test_fails_with_schema_violation(self) -> None:
        with client_fixture() as (client, websocket):
            resp = assert_response_type(
                client.post(
                    '/api/v1/machines',
                    json={'some invalid key': 'some invalid value'}))
            self.assertEqual(400, resp.status_code)
            self.assertEqual({
                'what': 'SchemaViolation',
                'why': "data must contain ['name'] properties"
            }, resp.json)

            self.assertListEqual([], websocket.get_received())

    def test_ok(self) -> None:
        with client_fixture() as (client, websocket):
            resp = assert_response_type(
                client.post('/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

            resp = assert_response_type(client.get('/api/v1/machines'))
            self.assertEqual(200, resp.status_code)
            self.assertListEqual([{
                "id": 1,
                "name": "some-machine",
                "version": 1
            }], resp.json)

            self.assertListEqual(
                [{
                    'name': 'put_machine',
                    'args': [{
                        'id': 1,
                        'name': 'some-machine',
                        'version': 1
                    }],
                    'namespace': '/'
                }], websocket.get_received())


class TestPatchMachine(unittest.TestCase):
    def test_fails_with_nonjson(self) -> None:
        with client_fixture() as (client, websocket):
            resp = assert_response_type(
                client.patch('/api/v1/machines/1', data="so not JSON"))
            self.assertEqual(400, resp.status_code)
            self.assertEqual({
                'what': 'SchemaViolation',
                'why': 'data must be object'
            }, resp.json)

            self.assertListEqual([], websocket.get_received())

    def test_fails_with_schema_violation(self) -> None:
        with client_fixture() as (client, websocket):
            resp = assert_response_type(
                client.patch(
                    '/api/v1/machines/1',
                    json={'some invalid key': 'some invalid value'}))
            self.assertEqual(400, resp.status_code)
            self.assertEqual(
                {
                    'what': 'SchemaViolation',
                    'why': "data must contain only specified properties"
                }, resp.json)

            self.assertListEqual([], websocket.get_received())

    def test_rename_machine_ok(self) -> None:
        with client_fixture() as (client, websocket):
            resp = assert_response_type(
                client.post('/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

            # yapf: disable
            self.assertListEqual(
                [{'name': 'put_machine',
                  'args': [{'id': 1, 'name': 'some-machine', 'version': 1}],
                  'namespace': '/'}],
                websocket.get_received())  # yapf: enable

            resp = assert_response_type(
                client.patch(
                    '/api/v1/machines/1',
                    json={
                        'name': 'renamed-machine'
                    }))

            self.assertEqual(200, resp.status_code)

            resp = assert_response_type(client.get('/api/v1/machines'))
            self.assertEqual(200, resp.status_code)
            self.assertListEqual([{
                "id": 1,
                "name": "renamed-machine",
                "version": 2
            }], resp.json)

            # yapf: disable
            self.assertListEqual(
                [{'name': 'put_machine',
                  'args': [{'id': 1, 'version': 2, 'name': 'renamed-machine'}],
                  'namespace': '/'}],
                websocket.get_received())  # yapf: enable

    def test_renaming_non_existing_machine_fails(self) -> None:
        with client_fixture() as (client, websocket):
            resp = assert_response_type(
                client.patch(
                    '/api/v1/machines/1',
                    json={
                        'name': 'renamed-machine'
                    }))

            self.assertEqual(400, resp.status_code)
            self.assertEqual({
                'what': 'MachineNotFound',
                'why': {
                    'machine_id': 1
                }
            }, resp.json)

            self.assertListEqual([], websocket.get_received())

    def test_empty_patch_fails(self) -> None:
        with client_fixture() as (client, websocket):
            resp = assert_response_type(
                client.post(
                    '/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

            # yapf: disable
            self.assertListEqual(
                [{'name': 'put_machine',
                  'args': [{'id': 1, 'name': 'some-machine', 'version': 1}],
                  'namespace': '/'}],
                websocket.get_received())  # yapf: enable

            # Request an empty patch
            resp = assert_response_type(
                client.patch(
                    '/api/v1/machines/1',
                    json={}))

            self.assertEqual(400, resp.status_code)
            self.assertEqual(
                {'what': 'ConstraintViolation', 'why': 'Empty patch'},
                resp.json)

            self.assertListEqual([], websocket.get_received())


class TestDeleteMachine(unittest.TestCase):
    def test_delete_non_existent_machine_ok(self) -> None:
        with client_fixture() as (client, websocket):
            resp = assert_response_type(client.delete('/api/v1/machines/1'))
            self.assertEqual(200, resp.status_code)

            self.assertListEqual(
                [{'name': 'delete_machine', 'args': [{'id': 1}],
                  'namespace': '/'}],
                websocket.get_received())

    def test_ok(self) -> None:
        with client_fixture() as (client, websocket):
            resp = assert_response_type(
                client.post(
                    '/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

            # yapf: disable
            self.assertListEqual(
                [{'name': 'put_machine',
                  'args': [{'id': 1, 'name': 'some-machine', 'version': 1}],
                  'namespace': '/'}],
                websocket.get_received())  # yapf: enable

            resp = assert_response_type(client.delete('/api/v1/machines/1'))
            self.assertEqual(200, resp.status_code)

            resp = assert_response_type(client.get('/api/v1/machines'))
            self.assertEqual(200, resp.status_code)
            self.assertListEqual([], resp.json)

            # yapf: disable
            self.assertListEqual(
                [{'name': 'delete_machine',
                  'args': [{'id': 1}],
                  'namespace': '/'}],
                websocket.get_received())  # yapf: enable


class TestMachineState(unittest.TestCase):
    def test_that_it_works(self) -> None:
        with client_fixture() as (client, _):
            resp = assert_response_type(
                client.post(
                    '/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)
            machine_id = resp.json

            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1000,
                        "stop": 2000,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

    def test_put_machine_state_fails_with_nonjson(self) -> None:
        with client_fixture() as (client, _):
            resp = assert_response_type(
                client.post('/api/v1/put_machine_state', data="so not json"))
            self.assertEqual(400, resp.status_code)
            self.assertEqual({
                'what': 'SchemaViolation',
                'why': 'data must be object'
            }, resp.json)

    def test_put_machine_state_fails_with_schema_violation(self) -> None:
        with client_fixture() as (client, _):
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={"an_invalid_key": "some invalid value"}))
            self.assertEqual(400, resp.status_code)
            self.assertEqual({
                'what':
                    'SchemaViolation',
                'why':
                    "data must contain ['machine_id', 'start', 'stop', "
                    "'condition'] properties"
            }, resp.json)

    def test_put_machine_state_fails_for_start_after_stop(self) -> None:
        with client_fixture() as (client, _):
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": 1984,
                        "start": 3000,
                        "stop": 2000,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(400, resp.status_code)
            self.assertEqual({
                'what': 'ConstraintViolation',
                'why': 'stop before start'
            }, resp.json)

    def test_machine_doesnt_exist(self) -> None:
        with client_fixture() as (client, _):
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": 1984,
                        "start": 1000,
                        "stop": 2000,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(400, resp.status_code)
            self.assertDictEqual({
                'what': 'MachineNotFound',
                'why': {
                    'machine_id': 1984
                }
            }, resp.json)

    def test_overlap_before(self) -> None:
        with client_fixture() as (client, _):
            # add a machine
            resp = assert_response_type(
                client.post(
                    '/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)
            machine_id = resp.json

            # add a state
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1000,
                        "stop": 2000,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

            # update status with overlapping before
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 500,
                        "stop": 1500,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(400, resp.status_code)
            self.assertDictEqual({
                'what': 'MachineStateOverlap',
                'why': {
                    "machine_id": 1,
                    "start": 1000,
                    "stop": 2000,
                }
            }, resp.json)

    def test_overlap_after(self) -> None:
        with client_fixture() as (client, _):
            # add a machine
            resp = assert_response_type(
                client.post(
                    '/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)
            machine_id = resp.json

            # add a state
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1000,
                        "stop": 2000,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

            # update status with overlapping before
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1500,
                        "stop": 2500,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(400, resp.status_code)
            self.assertDictEqual({
                'what': 'MachineStateOverlap',
                'why': {
                    "machine_id": 1,
                    "start": 1000,
                    "stop": 2000,
                }
            }, resp.json)

    def test_overlap_encompassing(self) -> None:
        with client_fixture() as (client, _):
            # add a machine
            resp = assert_response_type(
                client.post(
                    '/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)
            machine_id = resp.json

            # add a state
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1000,
                        "stop": 2000,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

            # update status with overlapping before
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 900,
                        "stop": 2500,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(400, resp.status_code)
            self.assertDictEqual({
                'what': 'MachineStateOverlap',
                'why': {
                    "machine_id": 1,
                    "start": 1000,
                    "stop": 2000,
                }
            }, resp.json)

    def test_overlap_contained(self) -> None:
        with client_fixture() as (client, _):
            # add a machine
            resp = assert_response_type(
                client.post(
                    '/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)
            machine_id = resp.json

            # add a state
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1000,
                        "stop": 2000,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

            # update status with overlapping before
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1100,
                        "stop": 1900,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(400, resp.status_code)
            self.assertDictEqual({
                'what': 'MachineStateOverlap',
                'why': {
                    "machine_id": 1,
                    "start": 1000,
                    "stop": 2000,
                }
            }, resp.json)

    def test_prolonged_ok(self) -> None:
        with client_fixture() as (client, _):
            # add a machine
            resp = assert_response_type(
                client.post(
                    '/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)
            machine_id = resp.json

            # add a state
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1000,
                        "stop": 2000,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

            # update status with overlapping before
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1000,
                        "stop": 2500,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

    def test_repeated_request_ok(self) -> None:
        with client_fixture() as (client, _):
            # add a machine
            resp = assert_response_type(
                client.post(
                    '/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)
            machine_id = resp.json

            # add a state
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1000,
                        "stop": 2000,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

            # update status with overlapping before
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1000,
                        "stop": 2000,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

    def test_error_on_condition_changed(self) -> None:
        with client_fixture() as (client, _):
            # add a machine
            resp = assert_response_type(
                client.post(
                    '/api/v1/machines', json={'name': 'some-machine'}))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)
            machine_id = resp.json

            # add a state
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1000,
                        "stop": 2000,
                        "condition": mesito.model.MachineCondition.WORKING.value
                    }))
            self.assertEqual(200, resp.status_code)
            self.assertEqual(1, resp.json)

            # update status with overlapping before
            resp = assert_response_type(
                client.post(
                    '/api/v1/put_machine_state',
                    json={
                        "machine_id": machine_id,
                        "start": 1000,
                        "stop": 2500,
                        "condition": mesito.model.MachineCondition.BROKEN.value
                    }))

            self.assertEqual(400, resp.status_code)
            self.assertEqual({
                'what': 'MachineStateConditionChanged',
                'why': {
                    'new': 'broken',
                    'old': 'working'
                }
            }, resp.json)


if __name__ == '__main__':
    unittest.main()

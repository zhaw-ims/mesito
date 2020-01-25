"""Implement operations to be executed by the back end."""
from typing import List, Tuple, Optional, Union

import sqlalchemy.orm
from icontract._decorators import ensure
from icontract._globals import SLOW

import mesito.front.error
import mesito.front.out
import mesito.front.valid
import mesito.model

# This is necessary due to widespread usage of ``id``.
# pylint: disable=redefined-builtin


# yapf: disable
def machine(
        session: sqlalchemy.orm.Session,
        id: int
) -> mesito.model.Machine:  # yapf: enable
    """Retrieve the given machine."""
    machi = session.query(mesito.model.Machine).get(id)
    assert machi is not None, "Expected the machine to exist: {}".format(id)
    assert isinstance(machi, mesito.model.Machine)
    return machi


def machine_exists(session: sqlalchemy.orm.Session, id: int) -> bool:
    """Return whether the machine is present in the database."""
    result = session.query(sqlalchemy.literal(True)).filter(
        mesito.model.Machine.id == id).first()

    return result is not None


# yapf: disable
def machines(
        session: sqlalchemy.orm.Session
) -> List[mesito.front.out.Machine]:  # yapf: enable
    """Retrieve the list of all the machines."""
    result = []  # type: List[mesito.front.out.Machine]
    for machi in session.query(mesito.model.Machine).order_by(
            mesito.model.Machine.name.asc()).all():
        result.append(
            mesito.front.out.machine(
                id=machi.id, name=machi.name, version=machi.version))

    return result


def created_machine_conforms_to_data(
        session: sqlalchemy.orm.Session,
        data: mesito.front.valid.MachinePost,
        result: Tuple[int, int]
) -> bool:
    """Check that the created machine in the database conforms to the input."""
    machi = machine(session=session, id=result[0])
    result = (machi.id == result[0] and
              machi.name == data['name'] and
              machi.version == result[1])
    assert isinstance(result, bool)
    return result


# yapf: disable
@ensure(lambda result: result[1] == 1, "Initial version is 1.")
@ensure(created_machine_conforms_to_data, enabled=SLOW)
def create_machine(
        session: sqlalchemy.orm.Session,
        data: mesito.front.valid.MachinePost
) -> Tuple[int, int]:  # yapf: enable
    """
    Create the machine i the database.

    :param session: transaction to the database
    :param data: machine data
    :return: ID of the machine, initial version
    """
    machi = mesito.model.Machine()
    machi.name = data['name']
    machi.version = 1
    session.add(machi)

    session.commit()

    assert isinstance(machi.id, int)

    return machi.id, machi.version


def patched_machine_conforms_to_data(
        session: sqlalchemy.orm.Session,
        id: int,
        data: mesito.front.valid.MachinePost,
        result: Tuple[
            Optional[int],
            Optional[mesito.front.error.MachineNotFound]]
) -> bool:
    """Check that the patched machine in the database conforms to the input."""
    version, err = result
    if err is not None:
        return True

    machi = machine(session=session, id=id)
    verdict = ((machi.name == data['name'] if 'name' in data else True) and
               machi.version == version)

    assert isinstance(verdict, bool)
    return verdict


# yapf: disable
@ensure(lambda result: (result[0] is None) ^ (result[1] is None),
        "Either a valid result or an error")
@ensure(patched_machine_conforms_to_data, enabled=SLOW)
def patch_machine(
        session: sqlalchemy.orm.Session,
        id: int,
        data: mesito.front.valid.MachinePatch
) -> Tuple[
    Optional[int],
    Optional[mesito.front.error.MachineNotFound]]:  # yapf: enable
    """
    Patch the machine in the database.

    :param session: transaction to the database
    :param id: identifier of the machine
    :param data: potentially partial machine data
    :return: new version, recoverable error if any
    """
    machi = session.query(mesito.model.Machine).get(id)
    if machi is None:
        return None, mesito.front.error.machine_not_found(
            machine_id=id)

    if 'name' in data:
        machi.name = data['name']

    machi.version += 1

    session.commit()

    return machi.version, None


# yapf: disable
@ensure(lambda session, id: not machine_exists(session=session, id=id))
def delete_machine(
        session: sqlalchemy.orm.Session,
        id: int
) -> None:  # yapf: enable
    """
    Delete the indicated machine in the database.

    :param session: transaction to the database
    :param id: identifier of the machine
    """
    session.query(mesito.model.MachineState).filter_by(machine_id=id).delete()
    session.query(mesito.model.Machine).filter_by(id=id).delete()

    session.commit()


def find_machine_state(
        session: sqlalchemy.orm.Session, machine_id: int,
        start: int) -> Optional[mesito.model.MachineState]:
    """
    Retrieve the machine state given the unique identifier (machine ID, start).

    :param session: database session
    :param machine_id: ID of the related machine
    :param start: start of the state, seconds since epoch
    :return: machine state, if available
    """
    result = session.query(mesito.model.MachineState).filter(
        (mesito.model.MachineState.machine_id == machine_id)
        & (mesito.model.MachineState.start == start)).first()

    if result is not None:
        assert isinstance(result, mesito.model.MachineState)
        return result

    return None


def machine_state_overlap(
        machine_id: int, start: int, stop: int,
        session: sqlalchemy.orm.Session) -> Optional[Tuple[int, int]]:
    """
    Verify for conflict between the state's (start, stop) and another state.

    Machine state must not overlap with an existing state unless we prolong
    an existing state.

    :param machine_id: ID of the machine
    :param start: start of the machine state's time range, seconds since epoch
    :param stop: end of the machine state's time range, seconds since epoch
    :param session: database session
    :return: None if no overlap; start, stop of an existing overlapping state
    """
    # yapf: disable
    first = session.query(
        mesito.model.MachineState.start,
        mesito.model.MachineState.stop).filter(
        (mesito.model.MachineState.start < stop) &
        (mesito.model.MachineState.stop > start) &
        (mesito.model.MachineState.machine_id == machine_id)
    ).first()  # yapf: enable

    if first is None:
        return None

    if first.start == start and first.stop <= stop:
        return None

    return first.start, first.stop


# yapf: disable
def put_machine_state(
        session: sqlalchemy.orm.Session,
        data: mesito.front.valid.MachineStatePut
) -> Tuple[
    Optional[int],
    Optional[Union[
        mesito.front.error.MachineStateOverlap,
        mesito.front.error.MachineStateConditionChanged,
        mesito.front.error.MachineNotFound]]]:  # yapf: enable
    """
    Upsert the machine state into the database.

    The machine state is uniquely identified by (machine ID, start timestamp).

    While it is expected that ``data`` has been verified by mesito.front
    for breach of data-local constraints, this function also verifies that
    the semantic constraints are observed as well. For example, that
    the condition of an existing state remains the same.

    :param session: database session
    :param data: validated request data
    :return: ID of the machine state or error, if any
    """
    # See https://stackoverflow.com/q/7646173/1600678
    if not machine_exists(session=session, id=data['machine_id']):
        return None, mesito.front.error.machine_not_found(
            machine_id=data['machine_id'])

    machine_state = find_machine_state(
        session=session, machine_id=data['machine_id'], start=data['start'])

    ##
    # Verify
    ##

    # Existing machine state must not change condition.
    if (machine_state is not None
            and machine_state.condition != data['condition']):
        return None, mesito.front.error.machine_state_condition_changed(
            old=machine_state.condition,
            new=data['condition'])

    other_start_stop = machine_state_overlap(
        machine_id=data['machine_id'], start=data['start'],
        stop=data['stop'], session=session)

    if other_start_stop is not None:
        other_start, other_stop = other_start_stop
        return None, mesito.front.error.machine_state_overlap(
            start=other_start, stop=other_stop, machine_id=data['machine_id'])

    ##
    # Upsert
    ##

    if machine_state is None:
        machine_state = mesito.model.MachineState()
        machine_state.machine_id = data['machine_id']
        machine_state.start = data['start']

    machine_state.stop = data['stop']
    machine_state.condition = data['condition']

    machine_state.min_power_consumption = data.get(
        'min_power_consumption', None)

    machine_state.max_power_consumption = data.get(
        'max_power_consumption', None)

    machine_state.avg_power_consumption = data.get(
        'avg_power_consumption', None)

    machine_state.total_energy = data.get('total_energy', None)

    session.add(machine_state)
    session.commit()

    assert isinstance(machine_state.id, int)

    return machine_state.id, None

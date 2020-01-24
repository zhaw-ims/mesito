"""Implement operations to be executed by the back end."""
from typing import List, Tuple, Optional, Union

import sqlalchemy.orm
from icontract._decorators import ensure

import mesito.front.error
import mesito.front.out
import mesito.front.valid
import mesito.model


# yapf: disable
@ensure(
    lambda data, result:
    'id' not in data or result[1] is not None or result[0][0] == data['id'],
    'ID must not change in the result if already available in the input.'
)
@ensure(
    lambda data, result:
    'id' in data or result[1] is not None or result[0][1] == 1,
    'Version starts from 1 on new instances.'
)
def put_machine(
        session: sqlalchemy.orm.Session,
        data: mesito.front.valid.MachinePut
) -> Tuple[
    Optional[Tuple[int, int]],
    Optional[mesito.front.error.MachineNotFound]]:  # yapf: enable
    """
    Upsert the machine into the database.

    :param session: transaction to the database
    :param data: machine data
    :return: (ID, version), error if any
    """
    # pylint: disable=invalid-name
    if 'id' in data:
        machine = session.query(mesito.model.Machine).get(data['id'])
        if machine is None:
            return None, mesito.front.error.machine_not_found(
                machine_id=data['id'])

        machine.name = data['name']
        machine.version += 1
    else:
        machine = mesito.model.Machine()
        machine.name = data['name']
        machine.version = 1
        session.add(machine)

    session.commit()

    assert isinstance(machine.id, int)

    return (machine.id, machine.version), None


# yapf: disable
def get_machines(
        session: sqlalchemy.orm.Session
) -> List[mesito.front.out.Machine]:  # yapf: enable
    """Retrieve the mapping (id -> name) of all the machines."""
    result = []  # type: List[mesito.front.out.Machine]
    for machine in session.query(mesito.model.Machine).order_by(
            mesito.model.Machine.name.asc()).all():
        result.append(
            mesito.front.out.machine(
                id=machine.id, name=machine.name, version=machine.version))

    return result


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
    machine_exists = session.query(sqlalchemy.literal(True)).filter(
        mesito.model.Machine.id == data['machine_id']).first()

    if not machine_exists:
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

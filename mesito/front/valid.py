"""Validate the input according to schemas from the wild outside world."""
import typing
from typing import Any, Tuple, Optional, Union

import fastjsonschema
from typing_extensions import TypedDict

import mesito.front.error
import mesito.model

# Pylint fires false positive on TypedDict and JSON schema definitions.
# pylint: disable=invalid-name

_machine_put = fastjsonschema.compile({
    'type': 'object',
    'properties': {
        'id': {
            'type':
            'integer',
            'description':
            'machine ID; '
            'if not provided, a new machine should be created.'
        },
        'name': {
            'type': 'string',
            'description': 'machine name'
        }
    },
    'required': ['name']
})


class _MachinePutMandatory(TypedDict):
    name: str


class MachinePut(_MachinePutMandatory, total=False):
    """
    Define a request to upsert a machine.

    Produce with :func:`machine_put`.
    """

    id: int


# yapf: disable
def machine_put(
        data: Any
) -> Tuple[
    Optional[MachinePut],
    Optional[mesito.front.error.SchemaViolation]]:  # yapf: enable
    """
    Validate and cast the input data.

    :param data: JSON data
    :return: cast, error message if any
    """
    try:
        _machine_put(data)
        return typing.cast(MachinePut, data), None
    except fastjsonschema.JsonSchemaException as err:
        return None, mesito.front.error.schema_violation(why=str(err))


_machine_state_put = fastjsonschema.compile({
    'type':
        'object',
    'properties': {
        'machine_id': {
            'type': 'integer',
            'description': 'machine ID'
        },
        'start': {
            'type': 'integer',
            'description': 'seconds since epoch'
        },
        'stop': {
            'type': 'integer',
            'description': 'seconds since epoch'
        },
        'condition': {
            'type': 'string',
            'enum': [cond.value for cond in mesito.model.MachineCondition],
            'description': 'machine condition'
        },
        'min_power_consumption': {
            'type': 'number',
            'description': 'minimum power consumption in the given time range'
        },
        'max_power_consumption': {
            'type': 'number',
            'description': 'maximum power consumption in the given time range'
        },
        'avg_power_consumption': {
            'type': 'number',
            'description': 'average power consumption in the given time range'
        },
        'total_energy': {
            'type': 'number',
            'description': 'total energy used in the given time range',
            'minimum': 0
        },
        'pieces': {
            'type': 'integer',
            'description':
                'total amount of pieces produced in the given time range',
            'minimum': 0
        }
    },
    'required': ['machine_id', 'start', 'stop', 'condition']
})


class _MachineStatePutMandatory(TypedDict):
    machine_id: int
    start: int
    stop: int
    condition: str


class MachineStatePut(_MachineStatePutMandatory, total=False):
    """
    Define a request to update the state of the machine.

    Produce with :func:`machine_state_put`.
    """

    min_power_consumption: float
    max_power_consumption: float
    avg_power_consumption: float
    total_energy: float
    pieces: int


# yapf: disable
def machine_state_put(
        data: Any
) -> Tuple[
    Optional[MachineStatePut],
    Optional[Union[
        mesito.front.error.SchemaViolation,
        mesito.front.error.ConstraintViolation]]]:  # yapf: enable
    """
    Validate and cast the input data.

    :param data: JSON data
    :return: cast, error message if any
    """
    try:
        _machine_state_put(data)
        casted = typing.cast(MachineStatePut, data)
    except fastjsonschema.JsonSchemaException as err:
        return None, mesito.front.error.schema_violation(why=str(err))

    if casted['start'] > casted['stop']:
        return None, mesito.front.error.constraint_violation(
            why='stop before start')

    return casted, None

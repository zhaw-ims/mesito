"""
Provide error handling to the outside world.

Use factory methods to create the errors.
"""

# Pylint fires false positive on TypedDict and JSON schema definitions.
# pylint: disable=invalid-name

from typing_extensions import TypedDict

SchemaViolation = TypedDict('SchemaViolation', {'what': str, 'why': str})


def schema_violation(why: str) -> SchemaViolation:
    """Indicate that the JSON schema of the input has been violated."""
    return {'what': SchemaViolation.__name__, 'why': why}


ConstraintViolation = TypedDict(
    'ConstraintViolation', {
        'what': str,
        'why': str
    })


def constraint_violation(why: str) -> ConstraintViolation:
    """Indicate that a local constraint of a class has been violated."""
    return {'what': ConstraintViolation.__name__, 'why': why}


_MachineStateOverlapWhy = TypedDict(
    '_MachineStateOverlapWhy', {
        'start': int,
        'stop': int,
        'machine_id': int
    })

MachineStateOverlap = TypedDict(
    'MachineStateOverlap', {
        'what': str,
        'why': _MachineStateOverlapWhy
    })


def machine_state_overlap(
        start: int, stop: int, machine_id: int) -> MachineStateOverlap:
    """Indicate that two machine states overlap in time."""
    return {
        'what':
        MachineStateOverlap.__name__,
        'why':
        _MachineStateOverlapWhy(start=start, stop=stop, machine_id=machine_id)
    }


_MachineStateConditionChangedWhy = TypedDict(
    '_MachineStateConditionChangedWhy', {
        'old': str,
        'new': str
    })

MachineStateConditionChanged = TypedDict(
    'MachineStateConditionChanged', {
        'what': str,
        'why': _MachineStateConditionChangedWhy
    })


def machine_state_condition_changed(
        old: str, new: str) -> MachineStateConditionChanged:
    """Indicate that the update of the machine state changes the condition."""
    return {
        'what': MachineStateConditionChanged.__name__,
        'why': {
            'old': old,
            'new': new
        }
    }


_MachineNotFound = TypedDict('_MachineNotFound', {'machine_id': int})

MachineNotFound = TypedDict(
    'MachineNotFound', {
        'what': str,
        'why': _MachineNotFound
    })


def machine_not_found(machine_id: int) -> MachineNotFound:
    """Indicate the the given machine ID does not exist in the database."""
    return {'what': MachineNotFound.__name__, 'why': {'machine_id': machine_id}}

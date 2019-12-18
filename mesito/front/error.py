"""
Provide error handling to the outside world.

Use factory methods to create the errors.
"""

# Pylint fires false positive on TypedDict and JSON schema definitions.
# pylint: disable=invalid-name

from typing_extensions import TypedDict


class SchemaViolation(TypedDict):
    """
    Represent a schema violation of the input.

    Produce with :func:`schema_violation`.
    """

    what: str
    why: str


def schema_violation(why: str) -> SchemaViolation:
    """Indicate that the JSON schema of the input has been violated."""
    return {'what': SchemaViolation.__name__, 'why': why}


class ConstraintViolation(TypedDict):
    """
    Represent a constraint violation in the input.

    Produce with :func:`constraint_violation`.
    """

    what: str
    why: str


def constraint_violation(why: str) -> ConstraintViolation:
    """Indicate that a local constraint of a class has been violated."""
    return {'what': ConstraintViolation.__name__, 'why': why}


class _MachineStateOverlapWhy(TypedDict):
    """Represent the conflicting state in an overlap of two machine states."""

    start: int
    stop: int
    machine_id: int


class MachineStateOverlap(TypedDict):
    """
    Represent an time overlap of two machine states.

    Produce with :func:`machine_state_overlap`.
    """

    what: str
    why: _MachineStateOverlapWhy


def machine_state_overlap(
        start: int, stop: int, machine_id: int) -> MachineStateOverlap:
    """Indicate that two machine states overlap in time."""
    return {
        'what': MachineStateOverlap.__name__,
        'why': {
            'start': start,
            'stop': stop,
            'machine_id': machine_id
        }
    }


class _MachineStateConditionChangedWhy(TypedDict):
    old: str
    new: str


class MachineStateConditionChanged(TypedDict):
    """
    Represent an unexpected change of machine condition.

    Produce with :func:`machine_state_condition_changed`.
    """

    what: str
    why: _MachineStateConditionChangedWhy


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


class _MachineNotFoundWhy(TypedDict):
    machine_id: int


class MachineNotFound(TypedDict):
    """
    Represent an error when a given machine in the input does not exist.

    Produce with :func:`machine_not_found`.
    """

    what: str
    why: _MachineNotFoundWhy


def machine_not_found(machine_id: int) -> MachineNotFound:
    """Indicate the the given machine ID does not exist in the database."""
    return {'what': MachineNotFound.__name__, 'why': {'machine_id': machine_id}}

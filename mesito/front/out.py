"""Define output structures."""
from typing_extensions import TypedDict

from icontract._decorators import require

# This is necessary since `id` is a built-in.
# pylint: disable=invalid-name,redefined-builtin,comparison-with-callable


class Machine(TypedDict):
    """
    Define a machine retrieved.

    Produce with :func:`machine`
    """

    id: int  # pylint-disable: invalid-name
    name: str
    version: int


@require(
    lambda id: id <= 2**53,
    "ID exactly serializable in JSON double-precision float")
@require(
    lambda version: version <= 2 * 53,
    "Version exactly serializable in JSON double-precision float")
def machine(id: int, name: str, version: int) -> Machine:
    """Cast the machine into a JSON-able response."""
    return {"id": id, "name": name, "version": version}


class MachinePutEmit(TypedDict):
    """
    Represent an event emitted when a machine changed.

    Produce with :func:`machine_put_emit`
    """

    id: int
    name: str
    version: int


@require(
    lambda id: id <= 2**53,
    "ID exactly serializable in JSON double-precision float")
@require(
    lambda version: version <= 2 * 53,
    "Version exactly serializable in JSON double-precision float")
def machine_put_emit(id: int, name: str, version: int) -> MachinePutEmit:
    """Cast the machine into a put event to be emitted."""
    return {"id": id, "name": name, "version": version}

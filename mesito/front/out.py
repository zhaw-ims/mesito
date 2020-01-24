"""Define output structures."""
from typing_extensions import TypedDict

from icontract._decorators import require

import mesito.front.valid

# This is necessary since `id` is a built-in.
# pylint: disable=invalid-name,redefined-builtin,comparison-with-callable


class Machine(TypedDict):
    """Define a machine retrieved."""

    id: int  # pylint-disable: invalid-name
    name: str


class MachinePutEmit(TypedDict):
    """
    Represent an event emitted when a machine changed.

    Produce with :func:`machine_put_emit_from_input`
    """

    id: int
    name: str


@require(lambda data, id: "id" not in data or id == data["id"])
def machine_put_emit_from_input(
        data: mesito.front.valid.MachinePut, id: int) -> MachinePutEmit:
    """Cast the machine put request into an event to be emitted."""
    return {"id": id, "name": data["name"]}

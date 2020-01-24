"""Define output structures."""
from typing_extensions import TypedDict


class Machine(TypedDict):
    """Define a machine retrieved."""

    id: int
    name: str

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CallRecord:
    """Represents a single recorded call. Frozen for use as dict key."""

    name: str
    args: tuple[Any, ...]
    kwargs: tuple[tuple[str, Any], ...]

    @classmethod
    def create(cls, name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> "CallRecord":
        return cls(name, args, tuple(sorted(kwargs.items())))

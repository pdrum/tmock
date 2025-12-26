from dataclasses import dataclass
from typing import Any

from tmock.class_schema import ClassSchema


@dataclass
class CallRecord:
    """Represents a single recorded call."""
    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class MockState:
    """Manages the internal state of a mock instance."""

    def __init__(self, schema: ClassSchema) -> None:
        self.schema = schema
        self.calls: list[CallRecord] = []
        self.stubs: dict[str, Any] = {}

    def record_call(self, name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        self.calls.append(CallRecord(name, args, kwargs))

    def get_stub(self, name: str) -> Any:
        return self.stubs.get(name)

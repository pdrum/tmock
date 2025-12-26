from dataclasses import dataclass
from typing import Any

from tmock.class_schema import ClassSchema


@dataclass(frozen=True)
class CallRecord:
    """Represents a single recorded call. Frozen for use as dict key."""
    name: str
    args: tuple[Any, ...]
    kwargs: tuple[tuple[str, Any], ...]

    @classmethod
    def create(cls, name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> "CallRecord":
        return cls(name, args, tuple(sorted(kwargs.items())))


class MockState:
    """Manages the internal state of a mock instance."""

    def __init__(self, schema: ClassSchema) -> None:
        self.schema = schema
        self.calls: list[CallRecord] = []
        self.stubs: dict[CallRecord, Any] = {}

    def record_call(self, name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> CallRecord:
        record = CallRecord.create(name, args, kwargs)
        self.calls.append(record)
        return record

    def get_stub(self, record: CallRecord) -> Any:
        return self.stubs.get(record)

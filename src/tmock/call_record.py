from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from tmock.matchers.base import Matcher


@dataclass(frozen=True)
class RecordedArgument:
    name: str
    value: Any


@dataclass(frozen=True)
class CallRecord(ABC):
    name: str
    arguments: tuple[RecordedArgument, ...]

    @abstractmethod
    def format_call(self) -> str:
        """Format this call for display in error messages."""
        ...


@dataclass(frozen=True)
class MethodCallRecord(CallRecord):
    def format_call(self) -> str:
        args_str = ", ".join(f"{arg.name}={_format_value(arg.value)}" for arg in self.arguments)
        return f"{self.name}({args_str})"


@dataclass(frozen=True)
class GetterCallRecord(CallRecord):
    def format_call(self) -> str:
        return f"get {self.name}"


@dataclass(frozen=True)
class SetterCallRecord(CallRecord):
    def format_call(self) -> str:
        value = self.arguments[0].value if self.arguments else "?"
        return f"set {self.name} = {_format_value(value)}"


def _format_value(v: Any) -> str:
    if isinstance(v, Matcher):
        return v.describe()
    return repr(v)


def pattern_matches_call(pattern: CallRecord, actual: CallRecord) -> bool:
    """Check if a pattern (which may contain Matchers) matches an actual call."""
    if pattern.name != actual.name or len(pattern.arguments) != len(actual.arguments):
        return False
    for pattern_arg, actual_arg in zip(pattern.arguments, actual.arguments):
        if pattern_arg.name != actual_arg.name:
            return False
        if isinstance(pattern_arg.value, Matcher):
            if not pattern_arg.value.matches(actual_arg.value):
                return False
        elif pattern_arg.value != actual_arg.value:
            return False
    return True

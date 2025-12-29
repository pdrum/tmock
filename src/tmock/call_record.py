from dataclasses import dataclass
from typing import Any

from tmock.matchers.base import Matcher


@dataclass(frozen=True)
class RecordedArgument:
    name: str
    value: Any


@dataclass(frozen=True)
class CallRecord:
    name: str
    arguments: tuple[RecordedArgument, ...]

    def format_call(self) -> str:
        def format_value(v: Any) -> str:
            if isinstance(v, Matcher):
                return v.describe()
            return repr(v)

        args_str = ", ".join(f"{arg.name}={format_value(arg.value)}" for arg in self.arguments)
        return f"{self.name}({args_str})"


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

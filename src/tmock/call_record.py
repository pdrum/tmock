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

    def matches(self, other: "CallRecord") -> bool:
        """Check if this record (with possible matchers) matches another record (actual call)."""
        if self.name != other.name or len(self.arguments) != len(other.arguments):
            return False
        for self_arg, other_arg in zip(self.arguments, other.arguments):
            if self_arg.name != other_arg.name:
                return False
            if isinstance(self_arg.value, Matcher):
                if not self_arg.value.matches(other_arg.value):
                    return False
            elif self_arg.value != other_arg.value:
                return False
        return True

    def format_call(self) -> str:
        def format_value(v: Any) -> str:
            if isinstance(v, Matcher):
                return v.describe()
            return repr(v)

        args_str = ", ".join(f"{arg.name}={format_value(arg.value)}" for arg in self.arguments)
        return f"{self.name}({args_str})"

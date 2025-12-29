from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RecordedArgument:
    name: str
    value: Any


@dataclass(frozen=True)
class CallRecord:
    name: str
    arguments: tuple[RecordedArgument, ...]

    def format_call(self) -> str:
        args_str = ", ".join(f"{arg.name}={arg.value!r}" for arg in self.arguments)
        return f"{self.name}({args_str})"

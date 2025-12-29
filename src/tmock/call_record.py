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

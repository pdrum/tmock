from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from tmock.interceptor import Interceptor


@dataclass
class FieldRef:
    """Reference to a field on a mock, returned during DSL mode."""

    mock: Any
    name: str
    getter_interceptor: "Interceptor"
    setter_interceptor: Optional["Interceptor"]

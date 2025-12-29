from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Matcher(ABC, Generic[T]):
    """Base class for argument matchers.

    Matchers allow flexible argument matching in stubs and verifications.
    The generic type T is used to satisfy type checkers - at runtime,
    matcher functions return Matcher instances that are detected during matching.
    """

    @abstractmethod
    def matches(self, value: Any) -> bool:
        """Check if the given value matches this matcher."""
        pass

    @abstractmethod
    def describe(self) -> str:
        """Return a description for error messages, e.g., 'any(int)'."""
        pass

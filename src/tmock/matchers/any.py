from typing import Any, TypeVar, cast

from typeguard import TypeCheckError, check_type

from tmock.matchers.base import Matcher

T = TypeVar("T")


class AnyMatcher(Matcher[T]):
    """Matches any value, optionally constrained to a specific type."""

    def __init__(self, expected_type: type[T] = Any):  # type: ignore[assignment]
        self._expected_type = expected_type

    def matches(self, value: Any) -> bool:
        try:
            check_type(value, self._expected_type)
            return True
        except TypeCheckError:
            return False

    def describe(self) -> str:
        if self._expected_type is Any:
            return "any()"
        return f"any({self._expected_type.__name__})"


def any(expected_type: type[T] = Any) -> T:  # type: ignore[assignment]
    """Match any value, optionally of a specified type.

    Usage:
        given(mock.foo(any())).returns(10)        # matches anything
        given(mock.foo(any(int))).returns(10)     # matches any int
        verify(mock.foo(any(str))).once()

    Note: Returns a Matcher at runtime, but typed as T for IDE compatibility.
    """
    return cast(T, AnyMatcher(expected_type))

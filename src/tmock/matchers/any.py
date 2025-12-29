from typing import Any, TypeVar, cast

from typeguard import TypeCheckError, check_type

from tmock.matchers.base import Matcher

T = TypeVar("T")


class AnyMatcher(Matcher[T]):
    """Matches any value of the specified type."""

    def __init__(self, expected_type: type[T]):
        self._expected_type = expected_type

    def matches(self, value: Any) -> bool:
        try:
            check_type(value, self._expected_type)
            return True
        except TypeCheckError:
            return False

    def describe(self) -> str:
        return f"any({self._expected_type.__name__})"


def any(expected_type: type[T]) -> T:
    """Match any value of the specified type.

    Usage:
        given(mock.foo(any(int))).returns(10)
        verify(mock.foo(any(str))).once()

    Note: Returns a Matcher at runtime, but typed as T for IDE compatibility.
    """
    return cast(T, AnyMatcher(expected_type))

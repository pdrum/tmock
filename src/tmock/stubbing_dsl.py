from typing import TypeVar, Generic, Callable

from tmock.mock_state import MockState, CallRecord

T = TypeVar("T")
R = TypeVar("R")


class WhenBuilder(Generic[R]):
    """Captures a method call and allows setting its return value."""

    def __init__(self, state: MockState, record: CallRecord):
        self._state = state
        self._record = record

    def then_return(self, value: R) -> None:
        """Sets the return value for this specific call."""
        self._state.stubs[self._record] = value


class GivenBuilder(Generic[T]):
    """Builder for setting up mock behavior."""

    def __init__(self, mock: T):
        self._mock = mock
        self._state: MockState = object.__getattribute__(mock, '__tmock_state__')

    def when(self, call: Callable[[T], R]) -> WhenBuilder[R]:
        """Captures a method call via lambda for stubbing."""
        call(self._mock)

        if not self._state.calls:
            raise ValueError("No method call captured")

        recorded = self._state.calls.pop()
        return WhenBuilder(self._state, recorded)


def given(mock: T) -> GivenBuilder[T]:
    """Entry point for stubbing DSL."""
    return GivenBuilder(mock)

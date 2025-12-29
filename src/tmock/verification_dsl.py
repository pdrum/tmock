from typing import Any

from tmock.call_record import CallRecord
from tmock.exceptions import TMockVerificationError
from tmock.last_call_context import clear_last_interceptor, get_last_interceptor
from tmock.mock_generator import MethodInterceptor


class VerificationBuilder:
    def __init__(self, interceptor: MethodInterceptor, expected: CallRecord):
        self._interceptor = interceptor
        self._expected = expected

    def _get_count(self) -> int:
        return self._interceptor.count_matching_calls(self._expected)

    def _format_call(self) -> str:
        args_str = ", ".join(f"{arg.name}={arg.value!r}" for arg in self._expected.arguments)
        return f"{self._expected.name}({args_str})"

    def called(self) -> None:
        """Verify the method was called at least once."""
        self.at_least(1)

    def once(self) -> None:
        """Verify the method was called exactly once."""
        self.times(1)

    def times(self, n: int) -> None:
        """Verify the method was called exactly n times."""
        count = self._get_count()
        if count != n:
            raise TMockVerificationError(
                f"Expected {self._format_call()} to be called {n} time(s), but was called {count} time(s)"
            )

    def never(self) -> None:
        """Verify the method was never called."""
        self.times(0)

    def at_least(self, n: int) -> None:
        """Verify the method was called at least n times."""
        count = self._get_count()
        if count < n:
            raise TMockVerificationError(
                f"Expected {self._format_call()} to be called at least {n} time(s), but was called {count} time(s)"
            )

    def at_most(self, n: int) -> None:
        """Verify the method was called at most n times."""
        count = self._get_count()
        if count > n:
            raise TMockVerificationError(
                f"Expected {self._format_call()} to be called at most {n} time(s), but was called {count} time(s)"
            )


def verify(_: Any) -> VerificationBuilder:
    """Start verification of a mock method call.

    Usage:
        verify(mock.foo(10)).called()     # at least once
        verify(mock.foo(10)).once()       # exactly once
        verify(mock.foo(10)).times(2)     # exactly 2 times
        verify(mock.foo(10)).never()      # never called
        verify(mock.foo(10)).at_least(1)  # at least n times
        verify(mock.foo(10)).at_most(3)   # at most n times
    """
    interceptor = get_last_interceptor()
    if interceptor is None:
        raise TMockVerificationError("verify() expects a mock method call.")
    clear_last_interceptor()
    expected = interceptor.pop_last_call()
    return VerificationBuilder(interceptor, expected)

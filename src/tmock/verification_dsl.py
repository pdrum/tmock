from typing import Any

from tmock.call_record import CallRecord
from tmock.exceptions import TMockVerificationError
from tmock.method_interceptor import (
    DslType,
    MethodInterceptor,
    begin_dsl_operation_on_last_call,
    clear_pending_verification,
    set_pending_verification,
)


class VerificationBuilder:
    def __init__(self, interceptor: MethodInterceptor, expected: CallRecord):
        self._interceptor = interceptor
        self._expected = expected

    def _get_count(self) -> int:
        return self._interceptor.count_matching_calls(self._expected)

    def called(self) -> None:
        """Verify the method was called at least once."""
        self.at_least(1)

    def once(self) -> None:
        """Verify the method was called exactly once."""
        self.times(1)

    def times(self, n: int) -> None:
        """Verify the method was called exactly n times."""
        clear_pending_verification()
        count = self._get_count()
        if count != n:
            raise TMockVerificationError(
                f"Expected {self._expected.format_call()} to be called {n} time(s), but was called {count} time(s)"
            )

    def never(self) -> None:
        """Verify the method was never called."""
        self.times(0)

    def at_least(self, n: int) -> None:
        """Verify the method was called at least n times."""
        clear_pending_verification()
        count = self._get_count()
        if count < n:
            raise TMockVerificationError(
                f"Expected {self._expected.format_call()} to be called at least {n} time(s), "
                f"but was called {count} time(s)"
            )

    def at_most(self, n: int) -> None:
        """Verify the method was called at most n times."""
        clear_pending_verification()
        count = self._get_count()
        if count > n:
            raise TMockVerificationError(
                f"Expected {self._expected.format_call()} to be called at most {n} time(s), "
                f"but was called {count} time(s)"
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
    interceptor, record = begin_dsl_operation_on_last_call(DslType.VERIFICATION)
    set_pending_verification(record)
    return VerificationBuilder(interceptor, record)

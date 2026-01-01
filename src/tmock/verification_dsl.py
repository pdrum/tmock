from typing import Any, TypeVar

from tmock.call_record import CallRecord
from tmock.exceptions import TMockStubbingError, TMockVerificationError
from tmock.field_ref import FieldRef
from tmock.method_interceptor import (
    DslType,
    Interceptor,
    get_dsl_state,
)

R = TypeVar("R")


class VerificationBuilder:
    """Builder for configuring verification assertions after .call()."""

    def __init__(self, interceptor: Interceptor, expected: CallRecord):
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
        get_dsl_state().complete()
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
        get_dsl_state().complete()
        count = self._get_count()
        if count < n:
            raise TMockVerificationError(
                f"Expected {self._expected.format_call()} to be called at least {n} time(s), "
                f"but was called {count} time(s)"
            )

    def at_most(self, n: int) -> None:
        """Verify the method was called at most n times."""
        get_dsl_state().complete()
        count = self._get_count()
        if count > n:
            raise TMockVerificationError(
                f"Expected {self._expected.format_call()} to be called at most {n} time(s), "
                f"but was called {count} time(s)"
            )


class VerifyBuilder:
    """Builder returned by verify() to capture mock method calls for verification."""

    def call(self, _: R) -> VerificationBuilder:
        """Capture the mock method call pattern and return a verification builder.

        Usage:
            verify().call(mock.method(args)).times(n)
        """
        dsl = get_dsl_state()
        interceptor, record = dsl.begin_terminal()
        return VerificationBuilder(interceptor, record)

    def get(self, field_ref: Any) -> VerificationBuilder:
        """Capture a field getter pattern and return a verification builder.

        Usage:
            verify().get(mock.field).once()
        """
        if not isinstance(field_ref, FieldRef):
            raise TMockStubbingError("get() expects a field access, e.g. verify().get(mock.field)")
        dsl = get_dsl_state()
        # Call the getter interceptor to record the pattern
        field_ref.getter_interceptor()
        interceptor, record = dsl.begin_terminal()
        return VerificationBuilder(interceptor, record)

    def set(self, field_ref: Any, value: Any) -> VerificationBuilder:
        """Capture a field setter pattern and return a verification builder.

        Usage:
            verify().set(mock.field, value).once()
        """
        if not isinstance(field_ref, FieldRef):
            raise TMockStubbingError("set() expects a field access, e.g. verify().set(mock.field, value)")
        if field_ref.setter_interceptor is None:
            raise TMockStubbingError(f"Field '{field_ref.name}' is read-only and cannot be set")
        dsl = get_dsl_state()
        # Call the setter interceptor with the value to record the pattern
        field_ref.setter_interceptor(value)
        interceptor, record = dsl.begin_terminal()
        return VerificationBuilder(interceptor, record)


def verify() -> VerifyBuilder:
    """Begin verifying calls on a mock method.

    Usage:
        verify().call(mock.foo(10)).called()     # at least once
        verify().call(mock.foo(10)).once()       # exactly once
        verify().call(mock.foo(10)).times(2)     # exactly 2 times
        verify().call(mock.foo(10)).never()      # never called
        verify().call(mock.foo(10)).at_least(1)  # at least n times
        verify().call(mock.foo(10)).at_most(3)   # at most n times
    """
    dsl = get_dsl_state()
    dsl.enter_dsl_mode(DslType.VERIFICATION)
    return VerifyBuilder()

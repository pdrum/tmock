from typing import Callable, Generic, TypeVar

from tmock.call_record import CallRecord
from tmock.method_interceptor import (
    CallArguments,
    DslType,
    MethodInterceptor,
    RaisesStub,
    ReturnsStub,
    RunsStub,
    begin_dsl_operation_on_last_call,
    clear_pending_stub,
    set_pending_stub,
)

R = TypeVar("R")


class StubbingBuilder(Generic[R]):
    """Builder for configuring stub behavior after given()."""

    def __init__(self, interceptor: MethodInterceptor, record: CallRecord):
        self._interceptor = interceptor
        self._record = record

    def returns(self, value: R) -> None:
        """Stub the method to return the given value."""
        clear_pending_stub()
        self._interceptor.validate_return_type(value)
        self._interceptor.add_stub(ReturnsStub(self._record, value))

    def raises(self, exception: BaseException) -> None:
        """Stub the method to raise the given exception."""
        clear_pending_stub()
        self._interceptor.add_stub(RaisesStub(self._record, exception))

    def runs(self, action: Callable[[CallArguments], R]) -> None:
        """Stub the method to execute the given action with call arguments."""
        clear_pending_stub()

        def validated_action(args: CallArguments) -> R:
            result = action(args)
            self._interceptor.validate_return_type(result)
            return result

        self._interceptor.add_stub(RunsStub(self._record, validated_action))


def given(_: R) -> StubbingBuilder[R]:
    """Begin stubbing a mock method call.

    Usage:
        given(mock.method(args)).returns(value)
        given(mock.method(args)).raises(exception)
        given(mock.method(args)).runs(lambda args: args.get_by_name("x") + 1)
    """
    interceptor, record = begin_dsl_operation_on_last_call(DslType.STUBBING)
    set_pending_stub(record)
    return StubbingBuilder(interceptor, record)

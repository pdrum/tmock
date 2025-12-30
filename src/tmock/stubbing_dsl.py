from typing import Callable, Generic, TypeVar

from tmock.call_record import CallRecord
from tmock.method_interceptor import (
    CallArguments,
    DslType,
    MethodInterceptor,
    RaisesStub,
    ReturnsStub,
    RunsStub,
    get_dsl_state,
)

R = TypeVar("R")


class StubbingBuilder(Generic[R]):
    """Builder for configuring stub behavior after .given()."""

    def __init__(self, interceptor: MethodInterceptor, record: CallRecord):
        self._interceptor = interceptor
        self._record = record

    def returns(self, value: R) -> None:
        """Stub the method to return the given value."""
        self._interceptor.validate_return_type(value)
        self._interceptor.add_stub(ReturnsStub(self._record, value))
        get_dsl_state().complete()

    def raises(self, exception: BaseException) -> None:
        """Stub the method to raise the given exception."""
        self._interceptor.add_stub(RaisesStub(self._record, exception))
        get_dsl_state().complete()

    def runs(self, action: Callable[[CallArguments], R]) -> None:
        """Stub the method to execute the given action with call arguments."""

        def validated_action(args: CallArguments) -> R:
            result = action(args)
            self._interceptor.validate_return_type(result)
            return result

        self._interceptor.add_stub(RunsStub(self._record, validated_action))
        get_dsl_state().complete()


class DefineBuilder:
    """Builder returned by define() to capture mock method calls for stubbing."""

    def given(self, _: R) -> StubbingBuilder[R]:
        """Capture the mock method call pattern and return a stubbing builder.

        Usage:
            define().given(mock.method(args)).returns(value)
        """
        dsl = get_dsl_state()
        interceptor, record = dsl.begin_terminal()
        return StubbingBuilder(interceptor, record)


def define() -> DefineBuilder:
    """Begin defining stub behavior for a mock method.

    Usage:
        define().given(mock.method(args)).returns(value)
        define().given(mock.method(args)).raises(exception)
        define().given(mock.method(args)).runs(lambda args: args.get_by_name("x") + 1)
    """
    dsl = get_dsl_state()
    dsl.enter_dsl_mode(DslType.STUBBING)
    return DefineBuilder()

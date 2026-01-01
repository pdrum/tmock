from typing import Any, Callable, Generic, TypeVar

from tmock.call_record import CallRecord
from tmock.exceptions import TMockStubbingError
from tmock.field_ref import FieldRef
from tmock.interceptor import (
    CallArguments,
    DslType,
    Interceptor,
    RaisesStub,
    ReturnsStub,
    RunsStub,
    get_dsl_state,
)

R = TypeVar("R")


class StubbingBuilder(Generic[R]):
    """Builder for configuring stub behavior after .call()."""

    def __init__(self, interceptor: Interceptor, record: CallRecord):
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


class GivenBuilder:
    """Builder returned by given() to capture mock method calls for stubbing."""

    def call(self, _: R) -> StubbingBuilder[R]:
        """Capture the mock method call pattern and return a stubbing builder.

        Usage:
            given().call(mock.method(args)).returns(value)
        """
        dsl = get_dsl_state()
        interceptor, record = dsl.begin_terminal()
        return StubbingBuilder(interceptor, record)

    def get(self, field_ref: Any) -> StubbingBuilder[R]:
        """Capture a field getter pattern and return a stubbing builder.

        Usage:
            given().get(mock.field).returns(value)
        """
        if not isinstance(field_ref, FieldRef):
            raise TMockStubbingError("get() expects a field access, e.g. given().get(mock.field)")
        dsl = get_dsl_state()
        # Call the getter interceptor to record the pattern
        field_ref.getter_interceptor()
        interceptor, record = dsl.begin_terminal()
        return StubbingBuilder(interceptor, record)

    def set(self, field_ref: Any, value: Any) -> StubbingBuilder[None]:
        """Capture a field setter pattern and return a stubbing builder.

        Usage:
            given().set(mock.field, value).returns(None)
        """
        if not isinstance(field_ref, FieldRef):
            raise TMockStubbingError("set() expects a field access, e.g. given().set(mock.field, value)")
        if field_ref.setter_interceptor is None:
            raise TMockStubbingError(f"Field '{field_ref.name}' is read-only and cannot be set")
        dsl = get_dsl_state()
        # Call the setter interceptor with the value to record the pattern
        field_ref.setter_interceptor(value)
        interceptor, record = dsl.begin_terminal()
        return StubbingBuilder(interceptor, record)


def given() -> GivenBuilder:
    """Begin defining stub behavior for a mock method.

    Usage:
        given().call(mock.method(args)).returns(value)
        given().call(mock.method(args)).raises(exception)
        given().call(mock.method(args)).runs(lambda args: args.get_by_name("x") + 1)
    """
    dsl = get_dsl_state()
    dsl.enter_dsl_mode(DslType.STUBBING)
    return GivenBuilder()

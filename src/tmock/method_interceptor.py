from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum, auto
from inspect import Parameter, Signature
from typing import Any

from typeguard import TypeCheckError, check_type

from tmock.call_record import CallRecord, RecordedArgument
from tmock.exceptions import TMockStubbingError, TMockVerificationError


class DslType(Enum):
    STUBBING = auto()
    VERIFICATION = auto()


@dataclass
class BoundArgument:
    name: str
    value: Any
    annotation: Any


@dataclass
class Stub:
    call_record: CallRecord
    return_value: Any


class MethodInterceptor:
    def __init__(self, name: str, signature: Signature, class_name: str):
        self.__name = name
        self.__signature = signature
        self.__class_name = class_name
        self.__calls: list[CallRecord] = []
        self.__stubs: list[Stub] = []

    def pop_last_call(self) -> CallRecord:
        return self.__calls.pop()

    def count_matching_calls(self, expected: CallRecord) -> int:
        return sum(1 for call in self.__calls if call == expected)

    def set_return_value(self, record: CallRecord, value: Any) -> None:
        self._validate_return_type(value)
        self.__stubs.append(Stub(record, value))

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        _check_no_pending_builders()
        bound_args = self._bind_arguments(args, kwargs)
        self._validate_arg_types(bound_args)
        _set_last_interceptor(self)
        arguments = tuple(RecordedArgument(ba.name, ba.value) for ba in bound_args)
        record = CallRecord(self.__name, arguments)
        self.__calls.append(record)
        return self._find_stub(record)

    def _find_stub(self, record: CallRecord) -> Any:
        for stub in self.__stubs:
            if stub.call_record == record:
                return stub.return_value
        return None

    def _bind_arguments(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> list[BoundArgument]:
        try:
            bound = self.__signature.bind(*args, **kwargs)
            bound.apply_defaults()
        except TypeError as e:
            raise TMockStubbingError(f"Invalid args passed to {self.__name} => {e}")

        result = []
        for param_name, value in bound.arguments.items():
            param = self.__signature.parameters[param_name]
            result.append(BoundArgument(param_name, value, param.annotation))
        return result

    def _validate_arg_types(self, bound_args: list[BoundArgument]) -> None:
        for arg in bound_args:
            if arg.annotation is Parameter.empty:
                continue
            try:
                check_type(arg.value, arg.annotation)
            except TypeCheckError:
                raise TMockStubbingError(
                    f"Invalid type for argument '{arg.name}' of {self.__name}, expected {arg.annotation}, "
                    f"got {type(arg.value).__name__}"
                )

    def _validate_return_type(self, value: Any) -> None:
        return_annotation = self.__signature.return_annotation
        if return_annotation is Signature.empty:
            return
        try:
            check_type(value, return_annotation)
        except TypeCheckError:
            raise TMockStubbingError(
                f"Invalid return type for {self.__name}, expected {return_annotation}, got {type(value).__name__}"
            )


_last_interceptor: ContextVar[MethodInterceptor | None] = ContextVar("last_interceptor", default=None)
_pending_stub: ContextVar[CallRecord | None] = ContextVar("pending_stub", default=None)
_pending_verification: ContextVar[CallRecord | None] = ContextVar("pending_verification", default=None)


def _set_last_interceptor(interceptor: MethodInterceptor) -> None:
    _last_interceptor.set(interceptor)


def set_pending_stub(record: CallRecord) -> None:
    _pending_stub.set(record)


def clear_pending_stub() -> None:
    _pending_stub.set(None)


def set_pending_verification(record: CallRecord) -> None:
    _pending_verification.set(record)


def clear_pending_verification() -> None:
    _pending_verification.set(None)


def _check_no_pending_builders() -> None:
    """Raise if there's an incomplete given() or verify() operation."""
    pending = _pending_stub.get()
    if pending is not None:
        raise TMockStubbingError(
            f"Incomplete stub: given({pending.format_call()}) was never completed with .returns(). "
            f"Did you forget to call .returns()?"
        )

    pending = _pending_verification.get()
    if pending is not None:
        raise TMockVerificationError(
            f"Incomplete verification: verify({pending.format_call()}) was never completed. "
            f"Did you forget to call .once(), .called(), .never(), .times(), .at_least(), or .at_most()?"
        )


def begin_dsl_operation_on_last_call(dsl_type: DslType) -> tuple[MethodInterceptor, CallRecord]:
    """Begin a stubbing or verification DSL operation on the last mock call.

    Validates no pending incomplete operations exist, retrieves the last interceptor,
    clears the context, and returns the interceptor with its last call record.

    Raises:
        TMockStubbingError: If there's an incomplete stub or no mock method was called (for STUBBING).
        TMockVerificationError: If there's an incomplete verification or no mock method was called (for VERIFICATION).
    """
    _check_no_pending_builders()
    interceptor = _last_interceptor.get()
    if interceptor is None:
        if dsl_type == DslType.STUBBING:
            raise TMockStubbingError("given() expects a mock method call.")
        else:
            raise TMockVerificationError("verify() expects a mock method call.")
    _last_interceptor.set(None)
    return interceptor, interceptor.pop_last_call()

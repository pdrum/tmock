from dataclasses import dataclass
from inspect import Parameter, Signature
from typing import Any

from typeguard import TypeCheckError, check_type

from tmock.call_record import CallRecord, RecordedArgument
from tmock.exceptions import TMockStubbingError
from tmock.last_call_context import set_last_interceptor


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
        bound_args = self._bind_arguments(args, kwargs)
        self._validate_arg_types(bound_args)
        set_last_interceptor(self)
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

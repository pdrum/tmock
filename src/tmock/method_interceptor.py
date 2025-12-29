from inspect import Signature
from typing import Any

from tmock.call_record import CallRecord
from tmock.last_call_context import set_last_interceptor


class MethodInterceptor:
    def __init__(self, name: str, signature: Signature, class_name: str):
        self.__name = name
        self.__signature = signature
        self.__class_name = class_name
        self.__calls: list[CallRecord] = []
        self.__stubs: dict[CallRecord, Any] = {}

    def pop_last_call(self) -> CallRecord:
        return self.__calls.pop()

    def set_return_value(self, record: CallRecord, value: Any) -> None:
        self.__stubs[record] = value

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self._validate_signature(args, kwargs)
        set_last_interceptor(self)
        record = CallRecord.create(self.__name, args, kwargs)
        self.__calls.append(record)
        return self.__stubs.get(record)

    def _validate_signature(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        try:
            self.__signature.bind(*args, **kwargs)
        except TypeError as e:
            raise TypeError(f"{self.__name}(): {e}")

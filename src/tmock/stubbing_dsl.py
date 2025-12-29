from typing import Generic, TypeVar

from tmock.call_record import CallRecord
from tmock.exceptions import TMockStubbingError
from tmock.last_call_context import clear_last_interceptor, get_last_interceptor
from tmock.mock_generator import MethodInterceptor

R = TypeVar("R")


class ReturnsWrapper(Generic[R]):
    def __init__(self, interceptor: MethodInterceptor, record: CallRecord):
        self._interceptor = interceptor
        self._record = record

    def returns(self, value: R) -> None:
        self._interceptor.set_return_value(self._record, value)


def given(_: R) -> ReturnsWrapper[R]:
    interceptor = get_last_interceptor()
    if interceptor is None:
        raise TMockStubbingError("given() expects a mock method call.")
    clear_last_interceptor()
    record = interceptor.pop_last_call()
    return ReturnsWrapper(interceptor, record)

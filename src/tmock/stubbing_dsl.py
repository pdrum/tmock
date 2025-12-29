from typing import TypeVar, Generic

from tmock.call_context import get_last_interceptor, clear_last_interceptor
from tmock.mock_engine import MethodInterceptor
from tmock.mock_state import CallRecord

R = TypeVar("R")


class ReturnsWrapper(Generic[R]):

    def __init__(self, interceptor: MethodInterceptor, record: CallRecord):
        self._interceptor = interceptor
        self._record = record

    def returns(self, value: R) -> None:
        self._interceptor.set_return_value(self._record, value)


def given(ignored: R) -> ReturnsWrapper[R]:
    interceptor = get_last_interceptor()
    if interceptor is None:
        raise TypeError("given() expects a mock method call")
    clear_last_interceptor()
    record = interceptor._state.calls.pop()
    return ReturnsWrapper(interceptor, record)

from typing import Generic, TypeVar

from tmock.call_record import CallRecord
from tmock.method_interceptor import (
    DslType,
    MethodInterceptor,
    begin_dsl_operation_on_last_call,
    clear_pending_stub,
    set_pending_stub,
)

R = TypeVar("R")


class ReturnsWrapper(Generic[R]):
    def __init__(self, interceptor: MethodInterceptor, record: CallRecord):
        self._interceptor = interceptor
        self._record = record

    def returns(self, value: R) -> None:
        clear_pending_stub()
        self._interceptor.set_return_value(self._record, value)


def given(_: R) -> ReturnsWrapper[R]:
    interceptor, record = begin_dsl_operation_on_last_call(DslType.STUBBING)
    set_pending_stub(record)
    return ReturnsWrapper(interceptor, record)

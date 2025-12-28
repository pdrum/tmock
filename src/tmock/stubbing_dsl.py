from typing import TypeVar, Generic, Callable, ParamSpec

from tmock.mock_state import CallRecord
from tmock.mock_engine import MethodInterceptor

P = ParamSpec("P")
R = TypeVar("R")


class ReturnsWrapper(Generic[R]):
    def __init__(self, interceptor: MethodInterceptor, record: CallRecord):
        self._interceptor = interceptor
        self._record = record

    def returns(self, value: R) -> None:
        self._interceptor.set_return_value(self._record, value)


class StubbingBuilder(Generic[P, R]):

    def __init__(self, interceptor: MethodInterceptor):
        self._interceptor = interceptor

    def with_args(self, *args: P.args, **kwargs: P.kwargs) -> ReturnsWrapper[R]:
        name = self._interceptor.method_name
        try:
            self._interceptor.method_signature.bind(*args, **kwargs)
        except TypeError as e:
            raise TypeError(f"{name}(): {e}")
        record = CallRecord.create(name, args, kwargs)
        return ReturnsWrapper(self._interceptor, record)


def given(method: Callable[P, R]) -> StubbingBuilder[P, R]:
    if not isinstance(method, MethodInterceptor):
        raise TypeError("given() expects a mock method")
    return StubbingBuilder(method)

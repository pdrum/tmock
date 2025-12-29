from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tmock.mock_generator import MethodInterceptor

_last_interceptor: ContextVar["MethodInterceptor | None"] = ContextVar("last_interceptor", default=None)


def set_last_interceptor(interceptor: "MethodInterceptor") -> None:
    _last_interceptor.set(interceptor)


def get_last_interceptor() -> "MethodInterceptor | None":
    return _last_interceptor.get()


def clear_last_interceptor() -> None:
    _last_interceptor.set(None)

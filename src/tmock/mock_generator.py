from typing import Any, Type, TypeVar

from tmock.class_schema import introspect_class
from tmock.method_interceptor import MethodInterceptor

T = TypeVar("T")


def tmock(cls: Type[T]) -> T:
    schema = introspect_class(cls)

    class TMock(cls):  # type: ignore[valid-type, misc]
        def __init__(self) -> None:
            object.__setattr__(self, "__method_interceptors", {})

        def __getattribute__(self, name: str) -> Any:
            if _is_dunder(name):
                return object.__getattribute__(self, name)

            interceptors: dict[str, MethodInterceptor] = object.__getattribute__(self, "__method_interceptors")

            if name in schema.class_or_static:
                return getattr(cls, name)

            if name in interceptors:
                return interceptors[name]

            if name not in schema.method_signatures:
                raise AttributeError(f"{cls.__name__} has no method '{name}'")

            interceptors[name] = MethodInterceptor(name, schema.method_signatures[name], cls.__name__)
            return interceptors[name]

    instance = object.__new__(TMock)
    TMock.__init__(instance)
    return instance


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")

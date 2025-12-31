from typing import Any, Type, TypeVar

from tmock.class_schema import FieldSchema, introspect_class
from tmock.exceptions import TMockUnexpectedCallError
from tmock.method_interceptor import MethodInterceptor

T = TypeVar("T")


def tmock(cls: Type[T]) -> T:
    schema = introspect_class(cls)

    class TMock(cls):  # type: ignore[valid-type, misc]
        def __init__(self) -> None:
            object.__setattr__(self, "__method_interceptors", {})
            object.__setattr__(self, "__field_getter_interceptors", {})
            object.__setattr__(self, "__field_setter_interceptors", {})

        def __getattribute__(self, name: str) -> Any:
            if _is_dunder(name):
                return object.__getattribute__(self, name)

            if name in schema.class_or_static:
                return getattr(cls, name)

            if name in schema.method_signatures:
                return _get_method_interceptor(self, name)

            if name in schema.fields:
                return _get_field_value(self, name)

            raise TMockUnexpectedCallError(f"{cls.__name__} has no attribute '{name}'")

        def __setattr__(self, name: str, value: Any) -> None:
            if name in schema.fields:
                return _set_field_value(self, name, value)
            raise TMockUnexpectedCallError(f"{cls.__name__} has no attribute '{name}'")

    def _get_method_interceptor(self: TMock, name: str) -> MethodInterceptor:
        interceptors: dict[str, MethodInterceptor] = object.__getattribute__(self, "__method_interceptors")
        if existing := interceptors.get(name):
            return existing
        interceptors[name] = MethodInterceptor(name, schema.method_signatures[name], cls.__name__)
        return interceptors[name]

    def _get_field_value(self: TMock, name: str) -> Any:
        getters: dict[str, MethodInterceptor] = object.__getattribute__(self, "__field_getter_interceptors")
        if existing := getters.get(name):
            return existing()
        field: FieldSchema = schema.fields[name]
        getters[name] = MethodInterceptor(name, field.getter_signature, cls.__name__)
        return getters[name]()

    def _set_field_value(self: TMock, name: str, value: Any) -> None:
        field: FieldSchema = schema.fields[name]
        if field.setter_signature is None:
            raise TMockUnexpectedCallError(f"{cls.__name__}.{name} is read-only")
        setters: dict[str, MethodInterceptor] = object.__getattribute__(self, "__field_setter_interceptors")
        if existing := setters.get(name):
            existing(value)
            return
        setters[name] = MethodInterceptor(name, field.setter_signature, cls.__name__)
        setters[name](value)

    instance = object.__new__(TMock)
    TMock.__init__(instance)
    return instance


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")

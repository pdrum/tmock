from typing import Any, Type, TypeVar

from tmock.class_schema import FieldSchema, introspect_class
from tmock.exceptions import TMockUnexpectedCallError
from tmock.field_ref import FieldRef
from tmock.interceptor import (
    GetterInterceptor,
    MethodInterceptor,
    SetterInterceptor,
    get_dsl_state,
)

T = TypeVar("T")


def tmock(cls: Type[T], extra_fields: list[str] | None = None) -> T:
    schema = introspect_class(cls, extra_fields=extra_fields)

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
        is_async = name in schema.async_methods
        interceptors[name] = MethodInterceptor(name, schema.method_signatures[name], cls.__name__, is_async)
        return interceptors[name]

    def _get_field_value(self: TMock, name: str) -> Any:
        dsl = get_dsl_state()
        if dsl.is_awaiting_mock_interaction():
            getter = _get_or_create_getter(self, name)
            setter = _get_or_create_setter(self, name)
            return FieldRef(self, name, getter, setter)
        getters: dict[str, GetterInterceptor] = object.__getattribute__(self, "__field_getter_interceptors")
        if existing := getters.get(name):
            return existing()
        field: FieldSchema = schema.fields[name]
        getters[name] = GetterInterceptor(name, field.getter_signature, cls.__name__)
        return getters[name]()

    def _get_or_create_getter(self: TMock, name: str) -> GetterInterceptor:
        getters: dict[str, GetterInterceptor] = object.__getattribute__(self, "__field_getter_interceptors")
        if existing := getters.get(name):
            return existing
        field: FieldSchema = schema.fields[name]
        getters[name] = GetterInterceptor(name, field.getter_signature, cls.__name__)
        return getters[name]

    def _get_or_create_setter(self: TMock, name: str) -> SetterInterceptor | None:
        field: FieldSchema = schema.fields[name]
        if field.setter_signature is None:
            return None
        setters: dict[str, SetterInterceptor] = object.__getattribute__(self, "__field_setter_interceptors")
        if existing := setters.get(name):
            return existing
        setters[name] = SetterInterceptor(name, field.setter_signature, cls.__name__)
        return setters[name]

    def _set_field_value(self: TMock, name: str, value: Any) -> None:
        setter = _get_or_create_setter(self, name)
        if setter is None:
            raise TMockUnexpectedCallError(f"{cls.__name__}.{name} is read-only")
        setter(value)

    if "__call__" in schema.method_signatures:

        def __call__(self: TMock, *args: Any, **kwargs: Any) -> Any:
            return _get_method_interceptor(self, "__call__")(*args, **kwargs)

        setattr(TMock, "__call__", __call__)

    instance = object.__new__(TMock)
    TMock.__init__(instance)
    return instance


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")

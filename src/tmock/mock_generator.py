import inspect
from typing import Any, Callable, Type, TypeVar, Union, cast, overload

from tmock.class_schema import ALLOWED_MAGIC_METHODS, FieldSchema, introspect_class, resolve_forward_refs
from tmock.exceptions import TMockUnexpectedCallError
from tmock.field_ref import FieldRef
from tmock.interceptor import (
    GetterInterceptor,
    MethodInterceptor,
    SetterInterceptor,
    get_dsl_state,
)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def is_tmock(obj: Any) -> bool:
    """Check if an object is a TMock instance."""
    return getattr(type(obj), "_is_tmock", False)


@overload
def tmock(spec: F) -> F: ...


@overload
def tmock(spec: Type[T], extra_fields: list[str] | None = None) -> T: ...


def tmock(spec: Union[Type[T], F], extra_fields: list[str] | None = None) -> Union[T, F]:
    """
    Creates a type-safe mock of a class or function.

    Args:
        spec: The class or function to mock.
        extra_fields: Optional list of field names to support on the mock
                     (only for class mocks).

    Returns:
        A strict mock object adhering to the spec's signature.
    """
    if isinstance(spec, type):
        return _tmock_class(spec, extra_fields)
    elif callable(spec):
        if extra_fields is not None:
            raise TypeError("extra_fields is not supported when mocking a function.")
        return _tmock_function(spec)
    else:
        raise TypeError(f"tmock() requires a class or a function, got {type(spec)}")


def _tmock_function(fn: F) -> F:
    """Mock a function by returning a configured MethodInterceptor."""
    name = getattr(fn, "__name__", "mock_function")
    module = getattr(fn, "__module__", "tmock")

    try:
        sig = inspect.signature(fn)
        sig = resolve_forward_refs(fn, sig)
    except ValueError:
        # Fallback for builtins or weird callables
        sig = inspect.Signature()

    is_async = inspect.iscoroutinefunction(fn)

    interceptor = MethodInterceptor(name, sig, module, is_async=is_async)
    return cast(F, interceptor)


def _tmock_class(cls: Type[T], extra_fields: list[str] | None = None) -> T:
    """Implementation of class mocking."""
    schema = introspect_class(cls, extra_fields=extra_fields)

    class TMock(cls):  # type: ignore[valid-type, misc]
        _is_tmock = True
        __name__ = cls.__name__
        __module__ = cls.__module__

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

        def __repr__(self) -> str:
            # Fallback repr if not intercepted
            return f"<TMock of {cls.__name__}>"

        @staticmethod
        def _create_magic_method_wrapper(method_name: str) -> Callable[..., Any]:
            def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
                return _get_method_interceptor(self, method_name)(*args, **kwargs)

            return wrapper

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

    for magic_method in ALLOWED_MAGIC_METHODS:
        if magic_method in schema.method_signatures:
            setattr(TMock, magic_method, TMock._create_magic_method_wrapper(magic_method))

    instance = object.__new__(TMock)
    TMock.__init__(instance)
    return instance


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")

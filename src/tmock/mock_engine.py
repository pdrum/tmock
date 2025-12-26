from typing import TypeVar, Type, Any

from tmock.class_schema import ClassSchema, introspect_class
from tmock.mock_state import MockState

T = TypeVar("T")


def tmock(cls: Type[T]) -> T:
    """Creates a mock instance of the given class that intercepts all calls."""
    schema = introspect_class(cls)

    class TMock(cls):  # type: ignore[valid-type, misc]
        def __init__(self) -> None:
            self.__tmock_state__ = MockState(schema)

        def __getattribute__(self, name: str) -> Any:
            if _is_dunder(name):
                return object.__getattribute__(self, name)

            state: MockState = object.__getattribute__(self, '__tmock_state__')

            if name in state.schema.class_or_static:
                return getattr(cls, name)

            if name in state.schema.properties:
                record = state.record_call(name, (), {})
                return state.get_stub(record)

            return _create_method_interceptor(name, state, cls.__name__)

    instance = object.__new__(TMock)
    TMock.__init__(instance)
    return instance


def _create_method_interceptor(name: str, state: MockState, class_name: str) -> Any:
    """Creates an interceptor function for a method call."""

    def interceptor(*args: Any, **kwargs: Any) -> Any:
        _validate_method_exists(name, state.schema, class_name)
        _validate_method_signature(name, args, kwargs, state.schema)
        record = state.record_call(name, args, kwargs)
        return state.get_stub(record)

    return interceptor


def _validate_method_exists(name: str, schema: ClassSchema, class_name: str) -> None:
    """Raises AttributeError if the method doesn't exist on the parent class."""
    if name not in schema.method_signatures:
        raise AttributeError(f"{class_name} has no method '{name}'")


def _validate_method_signature(
    name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    schema: ClassSchema
) -> None:
    """Validates that the provided arguments match the method signature."""
    try:
        schema.method_signatures[name].bind(*args, **kwargs)
    except TypeError as e:
        raise TypeError(f"{name}(): {e}")


def _is_dunder(name: str) -> bool:
    """Checks if a name is a dunder (double underscore) attribute."""
    return name.startswith('__') and name.endswith('__')

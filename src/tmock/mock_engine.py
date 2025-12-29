from inspect import Signature
from typing import TypeVar, Type, Any

from tmock.call_context import set_last_interceptor
from tmock.class_schema import ClassSchema, introspect_class
from tmock.mock_state import MockState, CallRecord

T = TypeVar("T")


class MethodInterceptor:

    def __init__(self, name: str, state: MockState, class_name: str):
        self._name = name
        self._state = state
        self._class_name = class_name

    @property
    def method_name(self) -> str:
        return self._name

    @property
    def method_signature(self) -> Signature:
        return self._state.schema.method_signatures[self._name]

    def set_return_value(self, record: CallRecord, value: Any) -> None:
        self._state.stubs[record] = value

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        _validate_method_exists(self._name, self._state.schema, self._class_name)
        _validate_method_signature(self._name, args, kwargs, self._state.schema)
        set_last_interceptor(self)
        record = self._state.record_call(self._name, args, kwargs)
        return self._state.get_stub(record)


def tmock(cls: Type[T]) -> T:
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

            return MethodInterceptor(name, state, cls.__name__)

    instance = object.__new__(TMock)
    TMock.__init__(instance)
    return instance


def _validate_method_exists(name: str, schema: ClassSchema, class_name: str) -> None:
    if name not in schema.method_signatures:
        raise AttributeError(f"{class_name} has no method '{name}'")


def _validate_method_signature(
    name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    schema: ClassSchema
) -> None:
    try:
        schema.method_signatures[name].bind(*args, **kwargs)
    except TypeError as e:
        raise TypeError(f"{name}(): {e}")


def _is_dunder(name: str) -> bool:
    return name.startswith('__') and name.endswith('__')

from typing import TypeVar, Type, Any

T = TypeVar("T")


def tmock(cls: Type[T]) -> T:
    """
    Generates a mocked subclass of the passed class that intercepts all calls.
    """
    class TMock(cls):  # type: ignore[valid-type, misc]
        def __init__(self):
            self.__tmock_calls__ = []
            self.__tmock_stubs__ = []

        def __getattribute__(self, name: str) -> Any:
            if name.startswith('__') and name.endswith('__'):
                return object.__getattribute__(self, name)
            return None

    instance = object.__new__(TMock)
    instance.__init__()  # type: ignore[misc]
    return instance

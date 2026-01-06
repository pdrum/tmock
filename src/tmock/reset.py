from typing import Any

from tmock.exceptions import TMockResetError
from tmock.interceptor import Interceptor, MethodInterceptor


def reset(mock: Any) -> None:
    """Clear all interactions and behaviors from a mock.

    This resets the mock to its initial state, clearing both:
    - All recorded calls (interactions)
    - All stubbed behaviors (given configurations)
    """
    reset_interactions(mock)
    reset_behaviors(mock)


def reset_interactions(mock: Any) -> None:
    """Clear all recorded calls from a mock.

    After calling this, verify() will see no previous interactions.
    Stubbed behaviors are preserved.
    """
    for interceptor in _get_all_interceptors(mock):
        interceptor.reset_interactions()


def reset_behaviors(mock: Any) -> None:
    """Clear all stubbed behaviors from a mock.

    After calling this, all given() configurations are removed.
    The mock will raise TMockUnexpectedCallError for any unstubbed calls.
    Recorded interactions are preserved.
    """
    for interceptor in _get_all_interceptors(mock):
        interceptor.reset_behaviors()


def _get_all_interceptors(mock: Any) -> list[Interceptor]:
    """Get all interceptors from a mock (methods, getters, setters)."""
    if isinstance(mock, Interceptor):
        return [mock]

    interceptors: list[Interceptor] = []

    try:
        method_interceptors: dict[str, MethodInterceptor] = object.__getattribute__(mock, "__method_interceptors")
        interceptors.extend(method_interceptors.values())

        getter_interceptors: dict[str, MethodInterceptor] = object.__getattribute__(mock, "__field_getter_interceptors")
        interceptors.extend(getter_interceptors.values())

        setter_interceptors: dict[str, MethodInterceptor] = object.__getattribute__(mock, "__field_setter_interceptors")
        interceptors.extend(setter_interceptors.values())
    except AttributeError:
        raise TMockResetError(f"Object {mock!r} is not a valid tmock object or interceptor.")

    return interceptors

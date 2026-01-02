"""Patching mechanism for tmock - Phase 1: Module functions only."""

from __future__ import annotations

import inspect
from types import ModuleType
from typing import Any

from tmock.interceptor import MethodInterceptor


class PatchContext:
    """Context manager that patches a module function."""

    def __init__(self, module: ModuleType, func_name: str):
        self._module = module
        self._func_name = func_name
        self._original: Any = None
        self._interceptor: MethodInterceptor | None = None

    def __enter__(self) -> MethodInterceptor:
        self._original = getattr(self._module, self._func_name)

        sig = inspect.signature(self._original)
        is_async = inspect.iscoroutinefunction(self._original)

        self._interceptor = MethodInterceptor(
            name=self._func_name,
            signature=sig,
            class_name=self._module.__name__,
            is_async=is_async,
        )

        setattr(self._module, self._func_name, self._interceptor)
        return self._interceptor

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        setattr(self._module, self._func_name, self._original)


class Patcher:
    """Proxy that captures attribute access for patching."""

    def __init__(self, module: ModuleType):
        object.__setattr__(self, "_module", module)

    def __getattr__(self, name: str) -> PatchContext:
        module = object.__getattribute__(self, "_module")
        if not hasattr(module, name):
            raise AttributeError(f"Module '{module.__name__}' has no attribute '{name}'")
        return PatchContext(module, name)


def patch(module: ModuleType) -> Patcher:
    """Create a patcher for a module.

    Example:
        with patch(my_module).my_function as mock_func:
            given().call(mock_func(1, 2)).returns(42)
            result = my_module.my_function(1, 2)  # Returns 42
    """
    return Patcher(module)

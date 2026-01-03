import inspect
from types import ModuleType
from typing import Any

from tmock.exceptions import TMockPatchingError
from tmock.interceptor import MethodInterceptor


class ModuleFunctionPatchContext:
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


class StaticMethodPatchContext:
    """Context manager that patches a static method on a class."""

    def __init__(self, cls: type, method_name: str):
        self._cls = cls
        self._method_name = method_name
        self._original: Any = None
        self._interceptor: MethodInterceptor | None = None

    def __enter__(self) -> MethodInterceptor:
        self._original = inspect.getattr_static(self._cls, self._method_name)
        func = self._original.__func__

        sig = inspect.signature(func)
        is_async = inspect.iscoroutinefunction(func)

        self._interceptor = MethodInterceptor(
            name=self._method_name,
            signature=sig,
            class_name=self._cls.__name__,
            is_async=is_async,
        )

        setattr(self._cls, self._method_name, staticmethod(self._interceptor))
        return self._interceptor

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        setattr(self._cls, self._method_name, self._original)


class ClassMethodPatchContext:
    """Context manager that patches a class method on a class."""

    def __init__(self, cls: type, method_name: str):
        self._cls = cls
        self._method_name = method_name
        self._original: Any = None
        self._interceptor: MethodInterceptor | None = None

    def __enter__(self) -> MethodInterceptor:
        self._original = inspect.getattr_static(self._cls, self._method_name)
        func = self._original.__func__

        sig = inspect.signature(func)
        # Remove 'cls' parameter from signature
        params = list(sig.parameters.values())[1:]
        sig = sig.replace(parameters=params)

        is_async = inspect.iscoroutinefunction(func)

        self._interceptor = MethodInterceptor(
            name=self._method_name,
            signature=sig,
            class_name=self._cls.__name__,
            is_async=is_async,
        )

        # Wrap interceptor to ignore cls argument
        interceptor = self._interceptor

        def classmethod_wrapper(cls: Any, *args: Any, **kwargs: Any) -> Any:
            return interceptor(*args, **kwargs)

        setattr(self._cls, self._method_name, classmethod(classmethod_wrapper))
        return self._interceptor

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        setattr(self._cls, self._method_name, self._original)


class InstanceMethodPatchContext:
    """Context manager that patches an instance method on a class."""

    def __init__(self, cls: type, method_name: str):
        self._cls = cls
        self._method_name = method_name
        self._original: Any = None
        self._interceptor: MethodInterceptor | None = None

    def __enter__(self) -> MethodInterceptor:
        self._original = inspect.getattr_static(self._cls, self._method_name)

        sig = inspect.signature(self._original)
        # Remove 'self' parameter from signature
        params = list(sig.parameters.values())[1:]
        sig = sig.replace(parameters=params)

        is_async = inspect.iscoroutinefunction(self._original)

        self._interceptor = MethodInterceptor(
            name=self._method_name,
            signature=sig,
            class_name=self._cls.__name__,
            is_async=is_async,
        )

        # Wrap interceptor to ignore self argument
        interceptor = self._interceptor

        def instance_method_wrapper(self_arg: Any, *args: Any, **kwargs: Any) -> Any:
            return interceptor(*args, **kwargs)

        setattr(self._cls, self._method_name, instance_method_wrapper)
        return self._interceptor

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        setattr(self._cls, self._method_name, self._original)


class ModulePatcher:
    """Proxy that captures attribute access for patching module functions."""

    def __init__(self, module: ModuleType):
        object.__setattr__(self, "_module", module)

    def __getattr__(self, name: str) -> ModuleFunctionPatchContext:
        module = object.__getattribute__(self, "_module")
        if not hasattr(module, name):
            raise TMockPatchingError(f"Module '{module.__name__}' has no attribute '{name}'")
        return ModuleFunctionPatchContext(module, name)


class ClassPatcher:
    """Proxy that captures attribute access for patching class methods."""

    def __init__(self, cls: type):
        object.__setattr__(self, "_cls", cls)

    def __getattr__(self, name: str) -> StaticMethodPatchContext | ClassMethodPatchContext | InstanceMethodPatchContext:
        cls = object.__getattribute__(self, "_cls")
        if not hasattr(cls, name):
            raise TMockPatchingError(f"Class '{cls.__name__}' has no attribute '{name}'")

        attr = inspect.getattr_static(cls, name)

        if isinstance(attr, staticmethod):
            return StaticMethodPatchContext(cls, name)
        elif isinstance(attr, classmethod):
            return ClassMethodPatchContext(cls, name)
        elif callable(attr):
            return InstanceMethodPatchContext(cls, name)
        else:
            raise TMockPatchingError(f"'{name}' is not a method on '{cls.__name__}'.")


def patch(target: ModuleType | type) -> ModulePatcher | ClassPatcher:
    """Create a patcher for a module or class.

    Example:
        # Patch a module function
        with patch(my_module).my_function as mock_func:
            given().call(mock_func(1, 2)).returns(42)
            result = my_module.my_function(1, 2)  # Returns 42

        # Patch a static method
        with patch(MyClass).static_method as mock_method:
            given().call(mock_method("arg")).returns("mocked")

        # Patch a class method
        with patch(MyClass).class_method as mock_method:
            given().call(mock_method("arg")).returns("mocked")

        # Patch an instance method
        with patch(MyClass).instance_method as mock_method:
            given().call(mock_method("arg")).returns("mocked")
            obj = MyClass()
            obj.instance_method("arg")  # Returns "mocked"
    """
    if isinstance(target, ModuleType):
        return ModulePatcher(target)
    elif isinstance(target, type):
        return ClassPatcher(target)
    else:
        raise TMockPatchingError(f"patch() requires a module or class, got {type(target).__name__}")

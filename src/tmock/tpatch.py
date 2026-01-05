"""Typed patching using stdlib mock.

Provides explicit patching functions that wrap unittest.mock.patch with
tmock interceptors for use with the given()/verify() DSL.
"""

from __future__ import annotations

import importlib
import inspect
import typing
from contextlib import contextmanager
from inspect import Parameter, Signature
from types import ModuleType
from typing import Any, ClassVar, Generator
from unittest import mock

from tmock.class_schema import FieldDiscovery, resolve_forward_refs
from tmock.exceptions import TMockPatchingError
from tmock.field_ref import FieldRef
from tmock.interceptor import GetterInterceptor, MethodInterceptor, SetterInterceptor


class tpatch:
    """Typed patching using stdlib mock.

    Access methods via tpatch.function(), tpatch.method(), etc.

    Example:
        with tpatch.function("myapp.service.get_user") as mock:
            given().call(mock(1)).returns(User(id=1))

        with tpatch.method(MyClass, "save") as mock:
            given().call(mock(any(User))).returns(True)
    """

    @staticmethod
    @contextmanager
    def function(path: str) -> Generator[MethodInterceptor, None, None]:
        """Patch a function by import path. Supports from...import.

        Args:
            path: Dotted path to the function (e.g., "myapp.service.get_user").

        Yields:
            MethodInterceptor for use with given()/verify().

        Example:
            # In myapp/service.py: def get_user(id): ...
            # In test file: from myapp.service import get_user
            with tpatch.function("test_file.get_user") as mock:
                given().call(mock(1)).returns(User(id=1))
        """
        if "." not in path:
            raise TMockPatchingError(f"Invalid path '{path}'. Expected format: 'module.attribute'.")

        module_path, name = path.rsplit(".", 1)
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            raise TMockPatchingError(f"Cannot import module '{module_path}': {e}")

        if not hasattr(module, name):
            raise TMockPatchingError(f"Module '{module_path}' has no attribute '{name}'.")

        original = getattr(module, name)

        if not callable(original):
            raise TMockPatchingError(f"'{name}' is not callable. Use tpatch.module_var() for variables.")

        sig = inspect.signature(original)
        sig = resolve_forward_refs(original, sig)
        is_async = inspect.iscoroutinefunction(original)

        interceptor = MethodInterceptor(
            name=name,
            signature=sig,
            class_name=module_path,
            is_async=is_async,
        )

        with mock.patch(path, interceptor):
            yield interceptor

    @staticmethod
    @contextmanager
    def method(cls: type, name: str) -> Generator[MethodInterceptor, None, None]:
        """Patch an instance method on a class.

        Args:
            cls: The class containing the method.
            name: The method name.

        Yields:
            MethodInterceptor for use with given()/verify().

        Example:
            with tpatch.method(UserService, "save") as mock:
                given().call(mock(any(User))).returns(True)
                service = UserService()
                service.save(user)
        """
        if not hasattr(cls, name):
            raise TMockPatchingError(f"Class '{cls.__name__}' has no attribute '{name}'.")

        attr = inspect.getattr_static(cls, name)

        if isinstance(attr, staticmethod):
            raise TMockPatchingError(f"'{name}' is a staticmethod. Use tpatch.static_method().")
        if isinstance(attr, classmethod):
            raise TMockPatchingError(f"'{name}' is a classmethod. Use tpatch.class_method().")
        if isinstance(attr, property):
            raise TMockPatchingError(f"'{name}' is a property. Use tpatch.field().")
        if not callable(attr):
            raise TMockPatchingError(f"'{name}' is not callable. Use tpatch.field() or tpatch.class_var().")

        sig = inspect.signature(attr)
        sig = resolve_forward_refs(attr, sig)
        params = list(sig.parameters.values())

        if not params or params[0].name != "self":
            raise TMockPatchingError(
                f"'{name}' has no 'self' parameter. "
                f"Use tpatch.static_method() for static methods or tpatch.function() for functions."
            )

        # Remove 'self' from signature
        sig = sig.replace(parameters=params[1:])
        is_async = inspect.iscoroutinefunction(attr)

        interceptor = MethodInterceptor(
            name=name,
            signature=sig,
            class_name=cls.__name__,
            is_async=is_async,
        )

        wrapper = _create_method_wrapper(interceptor, is_async)

        with mock.patch.object(cls, name, wrapper):
            yield interceptor

    @staticmethod
    @contextmanager
    def static_method(cls: type, name: str) -> Generator[MethodInterceptor, None, None]:
        """Patch a static method on a class.

        Args:
            cls: The class containing the static method.
            name: The method name.

        Yields:
            MethodInterceptor for use with given()/verify().

        Example:
            with tpatch.static_method(IdGenerator, "generate") as mock:
                given().call(mock()).returns("fixed-id")
        """
        if not hasattr(cls, name):
            raise TMockPatchingError(f"Class '{cls.__name__}' has no attribute '{name}'.")

        attr = inspect.getattr_static(cls, name)

        if not isinstance(attr, staticmethod):
            if isinstance(attr, classmethod):
                raise TMockPatchingError(f"'{name}' is a classmethod, not a staticmethod. Use tpatch.class_method().")
            if callable(attr):
                raise TMockPatchingError(f"'{name}' is not a staticmethod. Use tpatch.method() for instance methods.")
            raise TMockPatchingError(f"'{name}' is not a staticmethod.")

        func = attr.__func__
        sig = inspect.signature(func)
        sig = resolve_forward_refs(func, sig)
        is_async = inspect.iscoroutinefunction(func)

        interceptor = MethodInterceptor(
            name=name,
            signature=sig,
            class_name=cls.__name__,
            is_async=is_async,
        )

        with mock.patch.object(cls, name, staticmethod(interceptor)):
            yield interceptor

    @staticmethod
    @contextmanager
    def class_method(cls: type, name: str) -> Generator[MethodInterceptor, None, None]:
        """Patch a class method on a class.

        Args:
            cls: The class containing the class method.
            name: The method name.

        Yields:
            MethodInterceptor for use with given()/verify().

        Example:
            with tpatch.class_method(Config, "from_env") as mock:
                given().call(mock()).returns(Config())
        """
        if not hasattr(cls, name):
            raise TMockPatchingError(f"Class '{cls.__name__}' has no attribute '{name}'.")

        attr = inspect.getattr_static(cls, name)

        if not isinstance(attr, classmethod):
            if isinstance(attr, staticmethod):
                raise TMockPatchingError(f"'{name}' is a staticmethod, not a classmethod. Use tpatch.static_method().")
            if callable(attr):
                raise TMockPatchingError(f"'{name}' is not a classmethod. Use tpatch.method() for instance methods.")
            raise TMockPatchingError(f"'{name}' is not a classmethod.")

        func = attr.__func__
        sig = inspect.signature(func)
        sig = resolve_forward_refs(func, sig)
        params = list(sig.parameters.values())

        # Remove 'cls' parameter
        if params and params[0].name in ("cls", "klass", "class_"):
            params = params[1:]
        sig = sig.replace(parameters=params)

        is_async = inspect.iscoroutinefunction(func)

        interceptor = MethodInterceptor(
            name=name,
            signature=sig,
            class_name=cls.__name__,
            is_async=is_async,
        )

        wrapper = _create_classmethod_wrapper(interceptor, is_async)

        with mock.patch.object(cls, name, classmethod(wrapper)):
            yield interceptor

    @staticmethod
    @contextmanager
    def field(cls: type, name: str) -> Generator[FieldRef, None, None]:
        """Patch an instance field (property, dataclass, pydantic, or annotated field).

        Uses FieldDiscovery for proper type information. Supports:
        - @property decorators
        - Dataclass fields
        - Pydantic model fields
        - Type-annotated instance variables

        Args:
            cls: The class containing the field.
            name: The field name.

        Yields:
            FieldRef for use with given().get()/set() and verify().get()/set().

        Example:
            with tpatch.field(Person, "name") as field:
                given().get(field).returns("Alice")
                given().set(field, "Bob").returns(None)
        """
        # Try FieldDiscovery first
        fields = FieldDiscovery(cls).discover_all()

        if name in fields:
            schema = fields[name]
            getter = GetterInterceptor(
                name=name,
                signature=schema.getter_signature,
                class_name=cls.__name__,
            )
            setter = (
                SetterInterceptor(
                    name=name,
                    signature=schema.setter_signature,
                    class_name=cls.__name__,
                )
                if schema.setter_signature
                else None
            )
        else:
            # Check if it's a property not discovered (e.g., private or dynamic)
            attr = inspect.getattr_static(cls, name) if hasattr(cls, name) else None

            if isinstance(attr, property):
                getter = GetterInterceptor(
                    name=name,
                    signature=_getter_sig_from_property(attr),
                    class_name=cls.__name__,
                )
                setter = (
                    SetterInterceptor(
                        name=name,
                        signature=_setter_sig_from_property(attr),
                        class_name=cls.__name__,
                    )
                    if attr.fset
                    else None
                )
            else:
                available = list(fields.keys()) if fields else []
                raise TMockPatchingError(
                    f"'{name}' is not a field on '{cls.__name__}'. "
                    f"Available fields: {available}. "
                    f"Use tpatch.class_var() for class variables."
                )

        field_ref = FieldRef(
            mock=None,
            name=name,
            getter_interceptor=getter,
            setter_interceptor=setter,
        )

        descriptor = _FieldDescriptor(getter, setter, name, cls.__name__)

        # Use create=True for dataclass/pydantic fields that don't exist as class attributes
        with mock.patch.object(cls, name, descriptor, create=True):
            yield field_ref

    @staticmethod
    @contextmanager
    def class_var(cls: type, name: str) -> Generator[FieldRef, None, None]:
        """Patch a class variable.

        Extracts type from ClassVar annotation if available.

        Args:
            cls: The class containing the variable.
            name: The variable name.

        Yields:
            FieldRef for use with given().get()/set() and verify().get()/set().

        Example:
            with tpatch.class_var(Settings, "DEFAULT_TIMEOUT") as field:
                given().get(field).returns(30)
        """
        if not hasattr(cls, name):
            raise TMockPatchingError(f"Class '{cls.__name__}' has no attribute '{name}'.")

        attr = inspect.getattr_static(cls, name)

        # Reject things that should use other methods
        if isinstance(attr, staticmethod):
            raise TMockPatchingError(f"'{name}' is a staticmethod. Use tpatch.static_method().")
        if isinstance(attr, classmethod):
            raise TMockPatchingError(f"'{name}' is a classmethod. Use tpatch.class_method().")
        if isinstance(attr, property):
            raise TMockPatchingError(f"'{name}' is a property. Use tpatch.field().")
        if callable(attr):
            raise TMockPatchingError(f"'{name}' is callable. Use tpatch.method() or tpatch.static_method().")

        # Check if it's a discovered field (instance field, not class var)
        fields = FieldDiscovery(cls).discover_all()
        if name in fields:
            raise TMockPatchingError(f"'{name}' is an instance field on '{cls.__name__}'. Use tpatch.field().")

        # Extract type from annotation
        value_type = _get_class_var_type(cls, name)

        getter = GetterInterceptor(
            name=name,
            signature=Signature(return_annotation=value_type),
            class_name=cls.__name__,
        )
        setter = _UnsupportedSetter(
            name=name,
            reason="Python doesn't support intercepting class-level attribute writes.",
        )

        field_ref = FieldRef(
            mock=None,
            name=name,
            getter_interceptor=getter,
            setter_interceptor=setter,  # type: ignore[arg-type]
        )

        descriptor = _FieldDescriptor(getter, setter, name, cls.__name__)

        with mock.patch.object(cls, name, descriptor):
            yield field_ref

    @staticmethod
    @contextmanager
    def module_var(module: ModuleType, name: str) -> Generator[FieldRef, None, None]:
        """Patch a module-level variable.

        Note: Due to Python limitations, module variables cannot be intercepted
        like class attributes. This uses a callback-based approach where stubbed
        values are applied directly to the module attribute.

        Setter stubbing/verification is not supported.

        Args:
            module: The module containing the variable.
            name: The variable name.

        Yields:
            FieldRef for use with given().get() and verify().get().

        Example:
            import myapp.config as config
            with tpatch.module_var(config, "DEBUG") as field:
                given().get(field).returns(True)
        """
        if not isinstance(module, ModuleType):
            raise TMockPatchingError(
                f"Expected a module, got {type(module).__name__}. Use tpatch.class_var() for class variables."
            )

        if not hasattr(module, name):
            raise TMockPatchingError(f"Module '{module.__name__}' has no attribute '{name}'.")

        original = getattr(module, name)

        # Reject callables
        if callable(original):
            raise TMockPatchingError(f"'{name}' is callable. Use tpatch.function().")

        # Extract type from annotation
        value_type = _get_module_var_type(module, name)

        # Create a patcher that updates the module attribute when stubs are added
        patcher = _ModuleVarPatcher(module, name, original)

        getter = _ModuleVarGetterInterceptor(
            name=name,
            signature=Signature(return_annotation=value_type),
            class_name=module.__name__,
            patcher=patcher,
        )
        setter = _UnsupportedSetter(
            name=name,
            reason="Python's descriptor protocol doesn't work on modules.",
        )

        field_ref = FieldRef(
            mock=None,
            name=name,
            getter_interceptor=getter,
            setter_interceptor=setter,  # type: ignore[arg-type]
        )

        try:
            yield field_ref
        finally:
            # Restore original value
            setattr(module, name, original)


# --- Helpers ---


def _create_method_wrapper(interceptor: MethodInterceptor, is_async: bool) -> Any:
    """Create a wrapper that strips 'self' and delegates to interceptor."""
    if is_async:

        async def async_wrapper(self_: Any, *args: Any, **kwargs: Any) -> Any:
            return await interceptor(*args, **kwargs)

        return async_wrapper
    else:

        def wrapper(self_: Any, *args: Any, **kwargs: Any) -> Any:
            return interceptor(*args, **kwargs)

        return wrapper


def _create_classmethod_wrapper(interceptor: MethodInterceptor, is_async: bool) -> Any:
    """Create a wrapper that strips 'cls' and delegates to interceptor."""
    if is_async:

        async def async_wrapper(cls_: Any, *args: Any, **kwargs: Any) -> Any:
            return await interceptor(*args, **kwargs)

        return async_wrapper
    else:

        def wrapper(cls_: Any, *args: Any, **kwargs: Any) -> Any:
            return interceptor(*args, **kwargs)

        return wrapper


def _getter_sig_from_property(prop: property) -> Signature:
    """Extract getter signature from a property."""
    if prop.fget:
        try:
            hints = typing.get_type_hints(prop.fget)
            return_type = hints.get("return", Any)
        except Exception:
            return_type = Any
    else:
        return_type = Any
    return Signature(return_annotation=return_type)


def _setter_sig_from_property(prop: property) -> Signature:
    """Extract setter signature from a property."""
    value_type: Any = Any
    if prop.fset:
        try:
            hints = typing.get_type_hints(prop.fset)
            # Get first non-return hint
            for param_name, param_type in hints.items():
                if param_name != "return":
                    value_type = param_type
                    break
        except Exception:
            pass
    return Signature(
        parameters=[Parameter("value", Parameter.POSITIONAL_OR_KEYWORD, annotation=value_type)],
        return_annotation=type(None),
    )


def _get_class_var_type(cls: type, name: str) -> Any:
    """Extract type hint for a class variable."""
    try:
        hints = typing.get_type_hints(cls)
        if name in hints:
            hint = hints[name]
            # Unwrap ClassVar[T] -> T
            if typing.get_origin(hint) is ClassVar:
                args = typing.get_args(hint)
                return args[0] if args else Any
            return hint
    except Exception:
        pass
    return Any


def _get_module_var_type(module: ModuleType, name: str) -> Any:
    """Extract type hint for a module variable."""
    try:
        hints = typing.get_type_hints(module)
        if name in hints:
            return hints[name]
    except Exception:
        pass

    # Try __annotations__ directly
    annotations = getattr(module, "__annotations__", {})
    if name in annotations:
        return annotations[name]

    return Any


class _ModuleVarPatcher:
    """Manages patching a module variable by directly updating the attribute."""

    def __init__(self, module: ModuleType, name: str, original: Any):
        self._module = module
        self._name = name
        self._original = original

    def update_value(self, value: Any) -> None:
        """Update the module attribute with the stubbed value."""
        setattr(self._module, self._name, value)

    def record_access(self) -> Any:
        """Record that the module attribute was accessed and return current value."""
        return getattr(self._module, self._name)


class _ModuleVarGetterInterceptor(GetterInterceptor):
    """Special getter interceptor for module variables that updates the module directly."""

    def __init__(
        self,
        name: str,
        signature: Signature,
        class_name: str,
        patcher: _ModuleVarPatcher,
    ):
        super().__init__(name, signature, class_name)
        self._patcher = patcher

    def add_stub(self, stub: Any) -> None:
        """Add a stub and update the module attribute with the stubbed value."""
        super().add_stub(stub)
        # When a stub is added, update the module attribute with the stubbed value
        # This is needed because descriptors don't work on modules
        from tmock.interceptor import ReturnsStub

        if isinstance(stub, ReturnsStub):
            self._patcher.update_value(stub.value)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Called when verifying - record the access."""
        # For verification, we need to track calls
        # But we can't intercept actual module access, so this is only called
        # from the DSL (given/verify), not from actual module.VAR access
        return super().__call__(*args, **kwargs)


class _UnsupportedSetter:
    """Sentinel for setters that cannot be intercepted due to Python limitations."""

    def __init__(self, name: str, reason: str):
        self._name = name
        self._reason = reason

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise TMockPatchingError(
            f"Setter stubbing/verification is not supported for '{self._name}'. "
            f"{self._reason} "
            f"There is no need to stub this setter - writes are silently discarded."
        )


class _FieldDescriptor:
    """Descriptor that intercepts field access via getter/setter interceptors."""

    def __init__(
        self,
        getter: GetterInterceptor,
        setter: SetterInterceptor | _UnsupportedSetter | None,
        name: str,
        class_name: str,
    ):
        self._getter = getter
        self._setter = setter
        self._name = name
        self._class_name = class_name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        return self._getter()

    def __set__(self, obj: Any, value: Any) -> None:
        if self._setter is None:
            raise TMockPatchingError(f"Cannot set read-only field '{self._name}' on '{self._class_name}'")
        if isinstance(self._setter, _UnsupportedSetter):
            # Discard the write - can't intercept it, don't let it go to original
            return
        self._setter(value)

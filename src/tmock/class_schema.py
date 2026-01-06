import dataclasses
from dataclasses import dataclass, field
from enum import Enum, auto
from inspect import Parameter, Signature, iscoroutinefunction, signature
from typing import Any, Callable, ClassVar, Type, get_origin, get_type_hints


class FieldSource(Enum):
    """Indicates how a field was discovered."""

    PROPERTY = auto()
    ANNOTATION = auto()
    DATACLASS = auto()
    PYDANTIC = auto()
    EXTRA = auto()


@dataclass
class FieldSchema:
    """Unified schema for any mockable field."""

    name: str
    getter_signature: Signature
    setter_signature: Signature | None
    source: FieldSource


@dataclass
class ClassSchema:
    """Holds introspected metadata about a class's members."""

    method_signatures: dict[str, Signature] = field(default_factory=dict)
    fields: dict[str, FieldSchema] = field(default_factory=dict)
    class_or_static: set[str] = field(default_factory=set)
    async_methods: set[str] = field(default_factory=set)


class FieldDiscovery:
    """Discovers mockable fields from various class types."""

    def __init__(self, cls: Type[Any]):
        self._cls = cls

    def discover_all(self) -> dict[str, FieldSchema]:
        """Discover all fields, with earlier sources taking precedence."""
        result: dict[str, FieldSchema] = {}
        self._merge(result, self._discover_pydantic_fields())
        self._merge(result, self._discover_dataclass_fields())
        self._merge(result, self._discover_properties())
        self._merge(result, self._discover_annotations())
        return result

    def _merge(self, target: dict[str, FieldSchema], discovered: dict[str, FieldSchema]) -> None:
        """Merge discovered fields, skipping those already present."""
        for name, field_schema in discovered.items():
            if name not in target:
                target[name] = field_schema

    def _discover_pydantic_fields(self) -> dict[str, FieldSchema]:
        """Discover fields from Pydantic models (v2)."""
        if not hasattr(self._cls, "__pydantic_complete__"):
            return {}

        result: dict[str, FieldSchema] = {}
        model_fields = getattr(self._cls, "model_fields", {})
        model_config = getattr(self._cls, "model_config", {})
        frozen = model_config.get("frozen", False) if isinstance(model_config, dict) else False

        for name, field_info in model_fields.items():
            if name.startswith("_"):
                continue
            annotation = getattr(field_info, "annotation", Any)
            result[name] = self._create_schema(
                name=name,
                annotation=annotation,
                has_setter=not frozen,
                source=FieldSource.PYDANTIC,
            )

        return result

    def _discover_dataclass_fields(self) -> dict[str, FieldSchema]:
        """Discover fields from dataclasses."""
        if not dataclasses.is_dataclass(self._cls):
            return {}

        result: dict[str, FieldSchema] = {}
        params = getattr(self._cls, "__dataclass_params__", None)
        frozen = params.frozen if params else False

        for fld in dataclasses.fields(self._cls):
            if fld.name.startswith("_"):
                continue
            result[fld.name] = self._create_schema(
                name=fld.name,
                annotation=fld.type,
                has_setter=not frozen,
                source=FieldSource.DATACLASS,
            )

        return result

    def _discover_properties(self) -> dict[str, FieldSchema]:
        """Discover @property descriptors."""
        result: dict[str, FieldSchema] = {}

        for name in dir(self._cls):
            if name.startswith("_"):
                continue

            raw_attr = _get_raw_attribute(self._cls, name)
            if isinstance(raw_attr, property):
                getter_sig = self._extract_property_getter_signature(raw_attr.fget)
                setter_sig = self._extract_property_setter_signature(raw_attr.fset) if raw_attr.fset else None
                result[name] = FieldSchema(
                    name=name,
                    getter_signature=getter_sig,
                    setter_signature=setter_sig,
                    source=FieldSource.PROPERTY,
                )

        return result

    def _discover_annotations(self) -> dict[str, FieldSchema]:
        """Discover class-level type annotations (instance variables)."""
        result: dict[str, FieldSchema] = {}

        try:
            hints = get_type_hints(self._cls)
        except Exception:
            hints = getattr(self._cls, "__annotations__", {})

        for name, annotation in hints.items():
            if name.startswith("_"):
                continue
            if get_origin(annotation) is ClassVar:
                continue
            result[name] = self._create_schema(
                name=name,
                annotation=annotation,
                has_setter=True,
                source=FieldSource.ANNOTATION,
            )

        return result

    def _create_schema(
        self,
        name: str,
        annotation: Any,
        has_setter: bool,
        source: FieldSource,
    ) -> FieldSchema:
        """Create a FieldSchema with synthetic getter/setter signatures."""
        getter_sig = Signature(return_annotation=annotation)

        if has_setter:
            value_param = Parameter("value", Parameter.POSITIONAL_OR_KEYWORD, annotation=annotation)
            setter_sig = Signature(parameters=[value_param], return_annotation=type(None))
        else:
            setter_sig = None

        return FieldSchema(
            name=name,
            getter_signature=getter_sig,
            setter_signature=setter_sig,
            source=source,
        )

    def _extract_property_getter_signature(self, getter: Any) -> Signature:
        """Creates a signature for a property getter (no params, just return type)."""
        if getter is None:
            return Signature(return_annotation=Signature.empty)

        try:
            hints = get_type_hints(getter)
            return_type = hints.get("return", Signature.empty)
        except Exception:
            return_type = Signature.empty

        return Signature(return_annotation=return_type)

    def _extract_property_setter_signature(self, setter: Any) -> Signature:
        """Creates a signature for a property setter (one 'value' param, returns None)."""
        value_type: Any = Signature.empty
        try:
            hints = get_type_hints(setter)
            # Get the first non-return hint (the value parameter, regardless of its name)
            for param_name, param_type in hints.items():
                if param_name != "return":
                    value_type = param_type
                    break
        except Exception:
            pass

        value_param = Parameter("value", Parameter.POSITIONAL_OR_KEYWORD, annotation=value_type)
        return Signature(parameters=[value_param], return_annotation=type(None))


ALLOWED_MAGIC_METHODS = {
    "__call__",
    "__enter__",
    "__exit__",
    "__aenter__",
    "__aexit__",
    "__getitem__",
    "__setitem__",
    "__delitem__",
    "__iter__",
    "__next__",
    "__aiter__",
    "__anext__",
    "__len__",
    "__contains__",
    "__bool__",
    "__hash__",
    "__eq__",
    "__ne__",
    "__lt__",
    "__le__",
    "__gt__",
    "__ge__",
}


def introspect_class(cls: Type[Any], extra_fields: list[str] | None = None) -> ClassSchema:
    """Analyzes a class and extracts metadata about its members."""
    schema = ClassSchema()

    # Discover fields
    discovery = FieldDiscovery(cls)
    schema.fields = discovery.discover_all()
    _apply_extra_fields_if_not_discovered(extra_fields, schema)

    # Discover methods and class/static members
    for name in dir(cls):
        is_magic_allowed = name in ALLOWED_MAGIC_METHODS
        if (name.startswith("_") and not is_magic_allowed) or name in schema.fields:
            continue

        raw_attr = _get_raw_attribute(cls, name)
        if raw_attr is None:
            continue

        # Skip magic methods that are just the default object implementation
        if is_magic_allowed and _default_impl_is_inherited_from_object(cls, name):
            continue

        if isinstance(raw_attr, (classmethod, staticmethod)):
            schema.class_or_static.add(name)
        elif callable(raw_attr) and not isinstance(raw_attr, property):
            schema.method_signatures[name] = _extract_instance_method_signature(raw_attr)
            if iscoroutinefunction(raw_attr):
                schema.async_methods.add(name)

    return schema


def _default_impl_is_inherited_from_object(cls: Type[Any], name: str) -> bool:
    """Returns True if the attribute is resolved from the 'object' class directly."""
    for base in cls.__mro__:
        if name in base.__dict__:
            return base is object
    return False


def _apply_extra_fields_if_not_discovered(extra_fields, schema):
    if not extra_fields:
        return
    for name in extra_fields:
        if name not in schema.fields:
            schema.fields[name] = _create_extra_field_schema(name)


def _create_extra_field_schema(name: str) -> FieldSchema:
    """Create a FieldSchema for an extra field with no type info."""
    getter_sig = Signature(return_annotation=Any)
    value_param = Parameter("value", Parameter.POSITIONAL_OR_KEYWORD, annotation=Any)
    setter_sig = Signature(parameters=[value_param], return_annotation=type(None))
    return FieldSchema(
        name=name,
        getter_signature=getter_sig,
        setter_signature=setter_sig,
        source=FieldSource.EXTRA,
    )


def _get_raw_attribute(cls: Type[Any], name: str) -> Any:
    """Retrieves the raw attribute from the class hierarchy, bypassing descriptors."""
    for klass in cls.__mro__:
        if name in klass.__dict__:
            return klass.__dict__[name]
    return None


def _extract_instance_method_signature(method: Any) -> Signature:
    """Extracts signature from an instance method, excluding 'self' parameter."""
    sig = signature(method)
    sig = resolve_forward_refs(method, sig)
    params = list(sig.parameters.values())
    if params:
        return sig.replace(parameters=params[1:])
    return sig


def resolve_forward_refs(func: Callable[..., Any], sig: Signature) -> Signature:
    """Resolve string forward references in a signature using get_type_hints.

    This allows typeguard to properly validate types even when annotations
    are written as strings (forward references like -> "ClassName").

    Args:
        func: The function/method to resolve hints for.
        sig: The original signature from inspect.signature().

    Returns:
        A new Signature with forward references resolved to actual types.
        If resolution fails, returns the original signature unchanged.
    """
    try:
        hints = get_type_hints(func)
    except Exception:
        return sig

    new_params = []
    for param in sig.parameters.values():
        if param.name in hints:
            new_params.append(param.replace(annotation=hints[param.name]))
        else:
            new_params.append(param)

    return_annotation = hints.get("return", sig.return_annotation)
    return sig.replace(parameters=new_params, return_annotation=return_annotation)

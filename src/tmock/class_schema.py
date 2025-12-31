from dataclasses import dataclass, field
from enum import Enum, auto
from inspect import Parameter, Signature, signature
from typing import Any, Type, get_type_hints


class AttributeSource(Enum):
    """Indicates how an attribute was discovered."""

    PROPERTY = auto()
    ANNOTATION = auto()
    DATACLASS = auto()
    PYDANTIC = auto()
    UNSAFE = auto()


@dataclass
class AttributeSchema:
    """Unified schema for any mockable attribute."""

    name: str
    getter_signature: Signature
    setter_signature: Signature | None
    source: AttributeSource


@dataclass
class ClassSchema:
    """Holds introspected metadata about a class's members."""

    method_signatures: dict[str, Signature] = field(default_factory=dict)
    attributes: dict[str, AttributeSchema] = field(default_factory=dict)
    class_or_static: set[str] = field(default_factory=set)


def introspect_class(cls: Type[Any]) -> ClassSchema:
    """Analyzes a class and extracts metadata about its members."""
    schema = ClassSchema()

    for name in dir(cls):
        if name.startswith("_"):
            continue

        raw_attr = _get_raw_attribute(cls, name)
        if raw_attr is None:
            continue

        _categorize_attribute(name, raw_attr, schema)

    return schema


def _get_raw_attribute(cls: Type[Any], name: str) -> Any:
    """Retrieves the raw attribute from the class hierarchy, bypassing descriptors."""
    for klass in cls.__mro__:
        if name in klass.__dict__:
            return klass.__dict__[name]
    return None


def _categorize_attribute(name: str, attr: Any, schema: ClassSchema) -> None:
    """Categorizes an attribute and updates the schema accordingly."""
    if isinstance(attr, (classmethod, staticmethod)):
        schema.class_or_static.add(name)
    elif isinstance(attr, property):
        schema.attributes[name] = _extract_property_schema(name, attr)
    elif callable(attr):
        schema.method_signatures[name] = _extract_instance_method_signature(attr)


def _extract_instance_method_signature(method: Any) -> Signature:
    """Extracts signature from an instance method, excluding 'self' parameter."""
    sig = signature(method)
    params = list(sig.parameters.values())
    if params:
        return sig.replace(parameters=params[1:])
    return sig


def _extract_property_schema(name: str, prop: property) -> AttributeSchema:
    """Extracts getter and setter signatures from a property."""
    getter_sig = _extract_getter_signature(prop.fget)
    setter_sig = _extract_setter_signature(prop.fset) if prop.fset else None
    return AttributeSchema(
        name=name,
        getter_signature=getter_sig,
        setter_signature=setter_sig,
        source=AttributeSource.PROPERTY,
    )


def _extract_getter_signature(getter: Any) -> Signature:
    """Creates a signature for a property getter (no params, just return type)."""
    if getter is None:
        return Signature(return_annotation=Signature.empty)

    try:
        hints = get_type_hints(getter)
        return_type = hints.get("return", Signature.empty)
    except Exception:
        return_type = Signature.empty

    return Signature(return_annotation=return_type)


def _extract_setter_signature(setter: Any) -> Signature:
    """Creates a signature for a property setter (one 'value' param, returns None)."""
    if setter is None:
        return Signature(return_annotation=type(None))

    try:
        hints = get_type_hints(setter)
        # Setter's first param (after self) is the value type
        value_type = hints.get("value", Signature.empty)
    except Exception:
        value_type = Signature.empty

    value_param = Parameter("value", Parameter.POSITIONAL_OR_KEYWORD, annotation=value_type)
    return Signature(parameters=[value_param], return_annotation=type(None))

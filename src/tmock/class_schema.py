from dataclasses import dataclass, field
from inspect import Signature, signature
from typing import Any, Type


@dataclass
class ClassSchema:
    """Holds introspected metadata about a class's members."""

    method_signatures: dict[str, Signature] = field(default_factory=dict)
    properties: set[str] = field(default_factory=set)
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
        schema.properties.add(name)
    elif callable(attr):
        schema.method_signatures[name] = _extract_instance_method_signature(attr)


def _extract_instance_method_signature(method: Any) -> Signature:
    """Extracts signature from an instance method, excluding 'self' parameter."""
    sig = signature(method)
    params = list(sig.parameters.values())
    if params:
        return sig.replace(parameters=params[1:])
    return sig

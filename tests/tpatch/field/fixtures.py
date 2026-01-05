"""Fixtures for tpatch.field tests."""

from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class Person:
    """Dataclass for field testing."""

    name: str
    age: int


@dataclass(frozen=True)
class ImmutablePerson:
    """Frozen dataclass."""

    name: str
    age: int


class PropertyPerson:
    """Class with properties."""

    def __init__(self) -> None:
        self._name = "default"
        self._age = 0

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def age(self) -> int:
        return self._age

    @property
    def read_only_prop(self) -> str:
        return "constant"


class AnnotatedFields:
    """Class with type annotations."""

    name: str
    count: int

    def __init__(self, name: str, count: int) -> None:
        self.name = name
        self.count = count


class PydanticUser(BaseModel):
    """Pydantic model for field testing."""

    name: str
    email: str
    age: int


class FrozenPydanticUser(BaseModel):
    """Frozen pydantic model."""

    model_config = {"frozen": True}
    name: str
    email: str

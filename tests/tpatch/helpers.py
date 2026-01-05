"""Helper fixtures for tpatch tests."""

from dataclasses import dataclass
from typing import ClassVar

from pydantic import BaseModel

# --- Functions for tpatch.function tests ---


def standalone_function(x: int, y: str) -> str:
    """A regular function."""
    return f"{y}-{x}"


async def async_standalone_function(x: int) -> str:
    """An async function."""
    return f"async-{x}"


def function_with_defaults(a: int, b: str = "default", c: bool = True) -> str:
    """Function with default arguments."""
    return f"{a}-{b}-{c}"


# --- Classes for tpatch.method tests ---


class Calculator:
    """Simple class with instance methods."""

    def add(self, a: int, b: int) -> int:
        return a + b

    def multiply(self, a: int, b: int) -> int:
        return a * b

    async def async_compute(self, x: int) -> int:
        return x * 2

    def method_with_defaults(self, a: int, b: str = "default") -> str:
        return f"{a}-{b}"


class ServiceWithDeps:
    """Class that depends on external calls."""

    def fetch_user(self, user_id: int) -> dict:
        # In real code, this would call an API
        return {"id": user_id, "name": "Real User"}

    def process(self, data: str) -> str:
        return f"processed: {data}"


# --- Classes for tpatch.staticmethod tests ---


class IdGenerator:
    """Class with static methods."""

    @staticmethod
    def generate() -> str:
        return "real-uuid"

    @staticmethod
    def generate_with_prefix(prefix: str) -> str:
        return f"{prefix}-real-uuid"

    @staticmethod
    async def async_generate() -> str:
        return "async-real-uuid"


# --- Classes for tpatch.classmethod tests ---


class Config:
    """Class with class methods."""

    _instance = None

    @classmethod
    def from_env(cls) -> "Config":
        return cls()

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        instance = cls()
        return instance

    @classmethod
    async def async_load(cls) -> "Config":
        return cls()


class Factory:
    """Factory with class methods."""

    @classmethod
    def create(cls, name: str) -> "Factory":
        return cls()


# --- Classes for tpatch.field tests ---


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


# --- Classes for tpatch.class_var tests ---


class Settings:
    """Class with class variables."""

    DEBUG: ClassVar[bool] = False
    MAX_RETRIES: ClassVar[int] = 3
    API_URL: ClassVar[str] = "https://api.example.com"

    # Untyped class variable
    UNTYPED_VAR = "default"


class ConfigWithClassVars:
    """Another class with class variables."""

    TIMEOUT: ClassVar[int] = 30
    ENABLED: ClassVar[bool] = True


# --- Module variable (in this module itself) ---

MODULE_DEBUG: bool = False
MODULE_TIMEOUT: int = 30
MODULE_NAME: str = "helpers"
UNTYPED_MODULE_VAR = "untyped"

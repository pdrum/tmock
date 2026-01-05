"""Fixtures for tpatch.class_method tests."""


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

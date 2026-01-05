"""Fixtures for tpatch.static_method tests."""


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

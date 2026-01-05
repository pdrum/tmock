"""Fixtures for tpatch.method tests."""


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
        return {"id": user_id, "name": "Real User"}

    def process(self, data: str) -> str:
        return f"processed: {data}"

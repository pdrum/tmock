"""Sample class for testing static and class method patching."""


class Calculator:
    """Sample class with static and class methods."""

    multiplier: int = 2

    @staticmethod
    def add(a: int, b: int) -> int:
        return a + b

    @staticmethod
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    @classmethod
    def multiply(cls, value: int) -> int:
        return value * cls.multiplier

    @classmethod
    def get_class_name(cls) -> str:
        return cls.__name__

    @staticmethod
    async def async_compute(x: int) -> int:
        return x * 2

    @classmethod
    async def async_class_method(cls, x: int) -> str:
        return f"{cls.__name__}: {x}"

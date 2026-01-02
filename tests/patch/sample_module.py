"""Sample module for testing patching."""


def add(a: int, b: int) -> int:
    return a + b


def greet(name: str) -> str:
    return f"Hello, {name}!"


def no_args() -> str:
    return "original"


async def async_fetch(url: str) -> str:
    return f"fetched: {url}"


def with_default(x: int, y: int = 10) -> int:
    return x + y


def with_kwargs(name: str, **kwargs: str) -> str:
    return f"{name}: {kwargs}"


def with_args(*args: int) -> int:
    return sum(args)


def divide(a: int, b: int) -> float:
    return a / b

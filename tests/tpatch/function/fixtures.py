"""Fixtures for tpatch.function tests."""


def standalone_function(x: int, y: str) -> str:
    """A regular function."""
    return f"{y}-{x}"


async def async_standalone_function(x: int) -> str:
    """An async function."""
    return f"async-{x}"


def function_with_defaults(a: int, b: str = "default", c: bool = True) -> str:
    """Function with default arguments."""
    return f"{a}-{b}-{c}"

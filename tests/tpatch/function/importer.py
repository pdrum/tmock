"""Module that imports from fixtures using from...import."""

from tests.tpatch.function.fixtures import standalone_function


def use_standalone_function(x: int, y: str) -> str:
    """Function that uses the imported standalone_function."""
    return standalone_function(x, y)

import pytest

from tmock.method_interceptor import reset_dsl_state


@pytest.fixture(autouse=True)
def clear_dsl_state():
    """Clear DSL state before and after each test."""
    reset_dsl_state()
    yield
    reset_dsl_state()

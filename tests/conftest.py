import pytest

from tmock.method_interceptor import clear_pending_stub, clear_pending_verification


@pytest.fixture(autouse=True)
def clear_pending_builders():
    """Clear any pending incomplete stubs or verifications before and after each test."""
    clear_pending_stub()
    clear_pending_verification()
    yield
    clear_pending_stub()
    clear_pending_verification()

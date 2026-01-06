"""Tests for patching context manager magic methods via tpatch.method()."""

import pytest

from tmock import any, given, tpatch, verify


class ContextManagerService:
    def __enter__(self) -> "ContextManagerService":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def action(self) -> str:
        return "result"


class TestPatchingContextManager:
    def test_patches_enter_and_exit(self) -> None:
        # We need to patch both if we want full control, or just one.
        # Note: tpatch.method patches the class method globally.

        with tpatch.method(ContextManagerService, "__enter__") as mock_enter:
            with tpatch.method(ContextManagerService, "__exit__") as mock_exit:
                # Stub __enter__ to return the service instance itself (or a mock of it)
                service = ContextManagerService()
                given().call(mock_enter()).returns(service)
                given().call(mock_exit(None, None, None)).returns(None)

                # Execute context manager
                with ContextManagerService() as s:
                    assert s is service

                verify().call(mock_enter()).once()
                verify().call(mock_exit(None, None, None)).once()

    def test_mocking_enter_return_value(self) -> None:
        """Test returning a different object from __enter__."""
        with tpatch.method(ContextManagerService, "__enter__") as mock_enter:
            # Stub __enter__ to return a string (normally type error but let's see if tmock catches it if strict)
            # ContextManagerService.__enter__ -> "ContextManagerService"
            # So returning "string" should raise StubbingError
            with pytest.raises(Exception) as exc:
                given().call(mock_enter()).returns("wrong type")
            assert "Invalid return type" in str(exc.value)

    def test_exception_handling_via_exit_patch(self) -> None:
        with tpatch.method(ContextManagerService, "__enter__") as mock_enter:
            with tpatch.method(ContextManagerService, "__exit__") as mock_exit:
                given().call(mock_enter()).returns(ContextManagerService())
                # Return True to suppress exception
                given().call(mock_exit(any(), any(), any())).returns(True)

                with ContextManagerService():
                    raise ValueError("Suppressed")

                verify().call(mock_exit(any(), any(), any())).once()

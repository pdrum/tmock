import pytest

from tmock import any, tmock
from tmock.stubbing_dsl import given


class TestRaisesStubbing:
    """Tests for the .raises() stubbing behavior."""

    def test_raises_exception_on_matching_call(self):
        class Calculator:
            def divide(self, a: int, b: int) -> float:
                return a / b

        mock = tmock(Calculator)
        given(mock.divide(10, 0)).raises(ZeroDivisionError("cannot divide by zero"))

        with pytest.raises(ZeroDivisionError) as exc_info:
            mock.divide(10, 0)

        assert "cannot divide by zero" in str(exc_info.value)

    def test_raises_does_not_affect_non_matching_calls(self):
        class Calculator:
            def divide(self, a: int, b: int) -> float:
                return a / b

        mock = tmock(Calculator)
        given(mock.divide(10, 0)).raises(ZeroDivisionError("cannot divide by zero"))

        # Non-matching call returns None (no stub)
        assert mock.divide(10, 2) is None

    def test_raises_with_any_matcher(self):
        class UserService:
            def get_user(self, user_id: int) -> str:
                return ""

        mock = tmock(UserService)
        given(mock.get_user(any(int))).raises(ValueError("user not found"))

        with pytest.raises(ValueError) as exc_info:
            mock.get_user(42)

        assert "user not found" in str(exc_info.value)

        with pytest.raises(ValueError):
            mock.get_user(999)

    def test_raises_custom_exception(self):
        class CustomError(Exception):
            def __init__(self, code: int, message: str):
                self.code = code
                self.message = message
                super().__init__(message)

        class ApiClient:
            def fetch(self, url: str) -> str:
                return ""

        mock = tmock(ApiClient)
        given(mock.fetch("https://api.example.com")).raises(CustomError(404, "Not Found"))

        with pytest.raises(CustomError) as exc_info:
            mock.fetch("https://api.example.com")

        assert exc_info.value.code == 404
        assert exc_info.value.message == "Not Found"

    def test_raises_can_be_combined_with_returns(self):
        class FileReader:
            def read(self, path: str) -> str:
                return ""

        mock = tmock(FileReader)
        given(mock.read("/valid/path")).returns("file contents")
        given(mock.read("/invalid/path")).raises(FileNotFoundError("file not found"))

        assert mock.read("/valid/path") == "file contents"

        with pytest.raises(FileNotFoundError):
            mock.read("/invalid/path")

    def test_raises_runtime_error(self):
        class Service:
            def process(self) -> None:
                pass

        mock = tmock(Service)
        given(mock.process()).raises(RuntimeError("service unavailable"))

        with pytest.raises(RuntimeError) as exc_info:
            mock.process()

        assert "service unavailable" in str(exc_info.value)

from typing import Callable

import pytest

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError

# --- Fixtures ---


def add(x: int, y: int) -> int:
    return x + y


def greet(name: str) -> str:
    return f"Hello, {name}"


async def fetch_data(id: int) -> dict:
    return {"id": id, "data": "real"}


def no_return() -> None:
    pass


# --- Tests ---


class TestMockFunctionBasic:
    def test_mocks_simple_function(self):
        mock = tmock(add)

        # Stub
        given().call(mock(1, 2)).returns(3)
        given().call(mock(10, 20)).returns(30)

        # Execute
        assert mock(1, 2) == 3
        assert mock(10, 20) == 30

        # Verify
        verify().call(mock(1, 2)).once()
        verify().call(mock(10, 20)).once()

    def test_mocks_function_with_matchers(self):
        mock = tmock(greet)

        given().call(mock(any(str))).returns("Hi!")

        assert mock("Alice") == "Hi!"
        assert mock("Bob") == "Hi!"

        verify().call(mock(any(str))).times(2)

    def test_mocks_void_function(self):
        mock = tmock(no_return)

        given().call(mock()).returns(None)

        mock()

        verify().call(mock()).once()


class TestMockFunctionAsync:
    @pytest.mark.asyncio
    async def test_mocks_async_function(self):
        mock = tmock(fetch_data)

        given().call(mock(1)).returns({"id": 1, "mock": True})

        result = await mock(1)
        assert result == {"id": 1, "mock": True}

        verify().call(mock(1)).once()

    @pytest.mark.asyncio
    async def test_async_return_type_validation(self):
        mock = tmock(fetch_data)

        # Should raise error because returns dict, not str
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock(1)).returns("not a dict")
        assert "Invalid return type" in str(exc.value)


class TestMockFunctionStrictness:
    def test_raises_if_not_stubbed(self):
        mock = tmock(add)

        with pytest.raises(TMockUnexpectedCallError):
            mock(1, 2)

    def test_raises_on_invalid_arg_type(self):
        mock = tmock(add)

        # add takes int, got str
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock("1", 2))
        assert "Invalid type for argument" in str(exc.value)

    def test_raises_on_invalid_return_type(self):
        mock = tmock(add)

        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock(1, 2)).returns("string")
        assert "Invalid return type" in str(exc.value)


class TestMockFunctionAPI:
    def test_rejects_extra_fields(self):
        with pytest.raises(TypeError, match="extra_fields is not supported"):
            tmock(add, extra_fields=["a"])

    def test_mock_can_be_passed_as_callback(self):
        # Scenario: A function expecting a callback
        def caller(callback: Callable[[int, int], int]):
            return callback(5, 5)

        mock_cb = tmock(add)
        given().call(mock_cb(5, 5)).returns(10)

        result = caller(mock_cb)
        assert result == 10
        verify().call(mock_cb(5, 5)).once()

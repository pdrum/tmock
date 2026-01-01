import pytest

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError


class AsyncService:
    """Service class with async methods for testing."""

    async def fetch_data(self, id: int) -> str:
        return ""

    async def save_data(self, id: int, data: str) -> bool:
        return False

    async def get_items(self) -> list[str]:
        return []

    async def process(self, value: int) -> int:
        return 0


class MixedService:
    """Service with both sync and async methods."""

    def sync_method(self, x: int) -> int:
        return 0

    async def async_method(self, x: int) -> int:
        return 0


class TestAsyncStubbing:
    """Tests for stubbing async methods."""

    @pytest.mark.asyncio
    async def test_basic_async_stubbing(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(123)).returns("fetched data")

        result = await mock.fetch_data(123)

        assert result == "fetched data"

    @pytest.mark.asyncio
    async def test_async_stubbing_with_any_matcher(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(any(int))).returns("any data")

        assert await mock.fetch_data(1) == "any data"
        assert await mock.fetch_data(999) == "any data"

    @pytest.mark.asyncio
    async def test_async_multiple_stubs(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(1)).returns("first")
        given().call(mock.fetch_data(2)).returns("second")

        assert await mock.fetch_data(1) == "first"
        assert await mock.fetch_data(2) == "second"

    @pytest.mark.asyncio
    async def test_async_stub_override(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(1)).returns("original")
        given().call(mock.fetch_data(1)).returns("override")

        assert await mock.fetch_data(1) == "override"

    @pytest.mark.asyncio
    async def test_async_returning_complex_types(self):
        mock = tmock(AsyncService)
        given().call(mock.get_items()).returns(["a", "b", "c"])

        result = await mock.get_items()

        assert result == ["a", "b", "c"]


class TestAsyncVerification:
    """Tests for verifying async method calls."""

    @pytest.mark.asyncio
    async def test_verify_async_called_once(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(any(int))).returns("data")

        await mock.fetch_data(123)

        verify().call(mock.fetch_data(123)).once()

    @pytest.mark.asyncio
    async def test_verify_async_called_times(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(any(int))).returns("data")

        await mock.fetch_data(1)
        await mock.fetch_data(2)
        await mock.fetch_data(3)

        verify().call(mock.fetch_data(any(int))).times(3)

    @pytest.mark.asyncio
    async def test_verify_async_never_called(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(any(int))).returns("data")

        verify().call(mock.fetch_data(any(int))).never()

    @pytest.mark.asyncio
    async def test_verify_async_at_least(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(any(int))).returns("data")

        await mock.fetch_data(1)
        await mock.fetch_data(2)
        await mock.fetch_data(3)

        verify().call(mock.fetch_data(any(int))).at_least(2)

    @pytest.mark.asyncio
    async def test_verify_async_at_most(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(any(int))).returns("data")

        await mock.fetch_data(1)

        verify().call(mock.fetch_data(any(int))).at_most(5)


class TestAsyncRaises:
    """Tests for async methods that raise exceptions."""

    @pytest.mark.asyncio
    async def test_async_raises_exception(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(any(int))).raises(ValueError("not found"))

        with pytest.raises(ValueError) as exc_info:
            await mock.fetch_data(123)

        assert str(exc_info.value) == "not found"

    @pytest.mark.asyncio
    async def test_async_raises_custom_exception(self):
        class NetworkError(Exception):
            pass

        mock = tmock(AsyncService)
        given().call(mock.fetch_data(any(int))).raises(NetworkError("connection failed"))

        with pytest.raises(NetworkError) as exc_info:
            await mock.fetch_data(123)

        assert str(exc_info.value) == "connection failed"


class TestAsyncRuns:
    """Tests for async methods with .runs() callback."""

    @pytest.mark.asyncio
    async def test_async_runs_with_sync_callback(self):
        mock = tmock(AsyncService)
        given().call(mock.process(any(int))).runs(lambda args: args.get_by_name("value") * 2)

        result = await mock.process(21)

        assert result == 42

    @pytest.mark.asyncio
    async def test_async_runs_with_side_effects(self):
        captured: list[int] = []
        mock = tmock(AsyncService)
        given().call(mock.process(any(int))).runs(
            lambda args: captured.append(args.get_by_name("value")) or args.get_by_name("value")
        )

        await mock.process(1)
        await mock.process(2)
        await mock.process(3)

        assert captured == [1, 2, 3]

    def test_async_callback_raises_error(self):
        async def async_callback(args):
            return args.get_by_name("value") * 2

        mock = tmock(AsyncService)

        with pytest.raises(TMockStubbingError) as exc_info:
            given().call(mock.process(any(int))).runs(async_callback)

        assert "runs() does not support async callbacks" in str(exc_info.value)


class TestMixedSyncAsync:
    """Tests for classes with both sync and async methods."""

    @pytest.mark.asyncio
    async def test_mixed_class_sync_method(self):
        mock = tmock(MixedService)
        given().call(mock.sync_method(5)).returns(10)

        result = mock.sync_method(5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_mixed_class_async_method(self):
        mock = tmock(MixedService)
        given().call(mock.async_method(5)).returns(10)

        result = await mock.async_method(5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_mixed_class_both_methods_stubbed(self):
        mock = tmock(MixedService)
        given().call(mock.sync_method(1)).returns(100)
        given().call(mock.async_method(2)).returns(200)

        sync_result = mock.sync_method(1)
        async_result = await mock.async_method(2)

        assert sync_result == 100
        assert async_result == 200

    @pytest.mark.asyncio
    async def test_mixed_class_verification(self):
        mock = tmock(MixedService)
        given().call(mock.sync_method(any(int))).returns(0)
        given().call(mock.async_method(any(int))).returns(0)

        mock.sync_method(1)
        await mock.async_method(2)

        verify().call(mock.sync_method(1)).once()
        verify().call(mock.async_method(2)).once()


class TestAsyncUnstubbed:
    """Tests for unstubbed async method behavior."""

    @pytest.mark.asyncio
    async def test_unstubbed_async_raises_error(self):
        mock = tmock(AsyncService)

        with pytest.raises(TMockUnexpectedCallError) as exc_info:
            await mock.fetch_data(123)

        assert "No matching behavior defined on AsyncService for fetch_data(id=123)" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wrong_args_async_raises_error(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(1)).returns("data")

        with pytest.raises(TMockUnexpectedCallError) as exc_info:
            await mock.fetch_data(999)

        assert "No matching behavior defined on AsyncService for fetch_data(id=999)" in str(exc_info.value)


class TestAsyncTypeValidation:
    """Tests for type validation with async methods."""

    def test_async_validates_arg_types(self):
        mock = tmock(AsyncService)

        with pytest.raises(TMockStubbingError) as exc_info:
            given().call(mock.fetch_data("not an int")).returns("data")  # type: ignore

        assert "Invalid type for argument 'id'" in str(exc_info.value)

    def test_async_validates_return_types(self):
        mock = tmock(AsyncService)

        with pytest.raises(TMockStubbingError) as exc_info:
            given().call(mock.fetch_data(1)).returns(12345)  # type: ignore

        assert "Invalid return type" in str(exc_info.value)


class TestAsyncMultipleCalls:
    """Tests for multiple sequential async calls."""

    @pytest.mark.asyncio
    async def test_multiple_different_async_methods(self):
        mock = tmock(AsyncService)
        given().call(mock.fetch_data(1)).returns("item1")
        given().call(mock.save_data(1, "data")).returns(True)

        fetch_result = await mock.fetch_data(1)
        save_result = await mock.save_data(1, "data")

        assert fetch_result == "item1"
        assert save_result is True

    @pytest.mark.asyncio
    async def test_async_method_called_many_times(self):
        mock = tmock(AsyncService)
        given().call(mock.process(any(int))).returns(42)

        results = [await mock.process(i) for i in range(10)]

        assert results == [42] * 10
        verify().call(mock.process(any(int))).times(10)

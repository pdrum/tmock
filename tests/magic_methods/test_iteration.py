from typing import AsyncIterator, Iterator

import pytest

from tmock import given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError


class Dataset:
    def __iter__(self) -> Iterator[str]:
        return iter([])


class AsyncDataset:
    def __aiter__(self) -> AsyncIterator[str]:
        async def _gen() -> AsyncIterator[str]:
            yield "default"

        return _gen()


class NumberGenerator:
    def __iter__(self) -> "NumberGenerator":
        return self

    def __next__(self) -> int:
        return 0


class AsyncNumberGenerator:
    def __aiter__(self) -> "AsyncNumberGenerator":
        return self

    async def __anext__(self) -> int:
        return 0


class TestSyncIteration:
    def test_iter_returning_list_iterator(self):
        """Test stubbing __iter__ to return a standard list iterator."""
        mock = tmock(Dataset)
        data = ["a", "b", "c"]

        # Stub __iter__ to return an iterator over our list
        given().call(mock.__iter__()).returns(iter(data))

        results = []
        for item in mock:
            results.append(item)

        assert results == ["a", "b", "c"]
        verify().call(mock.__iter__()).once()

    def test_next_stubbing_values(self):
        """Test stubbing __next__ to return specific values."""
        mock = tmock(NumberGenerator)

        given().call(mock.__iter__()).returns(mock)
        given().call(mock.__next__()).returns(42)

        it = iter(mock)
        assert next(it) == 42
        assert next(it) == 42

        verify().call(mock.__iter__()).once()
        verify().call(mock.__next__()).times(2)

    def test_manual_stop_iteration(self):
        """Test stubbing __next__ to raise StopIteration to end a loop."""
        mock = tmock(NumberGenerator)

        given().call(mock.__iter__()).returns(mock)

        # We can use a side effect to return values then raise StopIteration
        # simulating a sequence: 1, 2, Stop
        iterator_state = iter([1, 2])

        def next_side_effect(_):
            return next(iterator_state)

        given().call(mock.__next__()).runs(next_side_effect)

        results = list(mock)
        assert results == [1, 2]

        verify().call(mock.__iter__()).once()
        # 1 (ok), 2 (ok), 3 (StopIteration raised caught by list) => 3 calls
        verify().call(mock.__next__()).times(3)

    def test_iter_raises_exception(self):
        """Test stubbing __iter__ to raise an arbitrary exception."""
        mock = tmock(Dataset)
        given().call(mock.__iter__()).raises(RuntimeError("Failed to open stream"))

        with pytest.raises(RuntimeError, match="Failed to open stream"):
            iter(mock)

        verify().call(mock.__iter__()).once()

    def test_iter_strictness_unstubbed(self):
        """Test that iteration raises error if __iter__ not stubbed."""
        mock = tmock(Dataset)
        with pytest.raises(TMockUnexpectedCallError):
            iter(mock)

    def test_iter_return_type_validation(self):
        """Test that stubbing __iter__ with incorrect type raises StubbingError."""
        mock = tmock(Dataset)

        # Dataset.__iter__ returns Iterator[str].
        # Returning a non-iterator (like an int) should fail.
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock.__iter__()).returns(123)
        assert "Invalid return type" in str(exc.value)


class TestAsyncIteration:
    @pytest.mark.asyncio
    async def test_aiter_returning_async_iterator(self):
        """Test stubbing __aiter__ to return a real async iterator."""
        mock = tmock(AsyncDataset)

        async def async_gen():
            yield "x"
            yield "y"

        # Stub __aiter__ to return our async generator object
        given().call(mock.__aiter__()).returns(async_gen())

        results = []
        async for item in mock:
            results.append(item)

        assert results == ["x", "y"]
        verify().call(mock.__aiter__()).once()

    @pytest.mark.asyncio
    async def test_anext_stubbing(self):
        """Test stubbing __anext__ directly."""
        mock = tmock(AsyncNumberGenerator)

        given().call(mock.__aiter__()).returns(mock)
        given().call(mock.__anext__()).returns(100)

        it = mock.__aiter__()
        val = await it.__anext__()
        assert val == 100

        verify().call(mock.__aiter__()).once()
        verify().call(mock.__anext__()).once()

    @pytest.mark.asyncio
    async def test_aiter_strictness_unstubbed(self):
        """Test that async iteration raises error if __aiter__ not stubbed."""
        mock = tmock(AsyncDataset)
        with pytest.raises(TMockUnexpectedCallError):
            async for _ in mock:
                pass

    @pytest.mark.asyncio
    async def test_aiter_return_type_validation(self):
        """Test that stubbing __aiter__ with incorrect type raises StubbingError."""
        mock = tmock(AsyncDataset)

        # AsyncDataset.__aiter__ returns AsyncIterator[str]
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock.__aiter__()).returns("not async iterator")
        assert "Invalid return type" in str(exc.value)

    @pytest.mark.asyncio
    async def test_anext_manual_stop_async_iteration(self):
        """Test stubbing __anext__ to raise StopAsyncIteration."""
        mock = tmock(AsyncNumberGenerator)
        given().call(mock.__aiter__()).returns(mock)
        given().call(mock.__anext__()).raises(StopAsyncIteration())

        results = []
        async for item in mock:
            results.append(item)

        assert results == []
        verify().call(mock.__aiter__()).once()
        verify().call(mock.__anext__()).once()

    @pytest.mark.asyncio
    async def test_anext_with_sync_side_effect(self):
        """Test stubbing an async method (__anext__) with a sync lambda using .runs()."""
        mock = tmock(AsyncNumberGenerator)
        given().call(mock.__aiter__()).returns(mock)

        # .runs() with a sync lambda that returns an int.
        # tmock should wrap this result in a coroutine since __anext__ is async.
        given().call(mock.__anext__()).runs(lambda _: 999)

        val = await mock.__anext__()
        assert val == 999

        verify().call(mock.__anext__()).once()

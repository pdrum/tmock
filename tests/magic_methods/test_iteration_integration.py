from typing import AsyncIterator, Iterator

import pytest

from tmock import given, tmock, verify
from tmock.exceptions import TMockStubbingError

# --- Support Classes ---


class DataRecord:
    def __init__(self, value: int):
        self.value = value


class DataSource:
    def __iter__(self) -> Iterator[DataRecord]:
        return iter([])


class AsyncDataSource:
    def __aiter__(self) -> AsyncIterator[DataRecord]:
        async def _empty() -> AsyncIterator[DataRecord]:
            if False:
                yield

        return _empty()


class DataProcessor:
    def __init__(self, source: DataSource):
        self.source = source

    def sum_values(self) -> int:
        total = 0
        try:
            for record in self.source:
                if record.value < 0:
                    raise ValueError("Negative value")
                total += record.value
        except ValueError:
            return -1
        return total


class AsyncDataProcessor:
    def __init__(self, source: AsyncDataSource):
        self.source = source

    async def sum_values(self) -> int:
        total = 0
        async for record in self.source:
            total += record.value
        return total


# --- Integration Tests ---


class TestIterationIntegration:
    def test_processing_multiple_items(self):
        """Test standard iteration over multiple items."""
        mock_source = tmock(DataSource)
        processor = DataProcessor(mock_source)

        records = [DataRecord(10), DataRecord(20), DataRecord(30)]
        given().call(mock_source.__iter__()).returns(iter(records))

        assert processor.sum_values() == 60
        verify().call(mock_source.__iter__()).once()

    def test_empty_iterator(self):
        """Test handling of empty iterator."""
        mock_source = tmock(DataSource)
        processor = DataProcessor(mock_source)

        given().call(mock_source.__iter__()).returns(iter([]))

        assert processor.sum_values() == 0
        verify().call(mock_source.__iter__()).once()

    def test_iteration_exception_bubbling(self):
        """Test that exceptions during iteration (from logic, not the iterator itself) bubble up correctly."""
        mock_source = tmock(DataSource)
        processor = DataProcessor(mock_source)

        records = [DataRecord(10), DataRecord(-5), DataRecord(20)]
        given().call(mock_source.__iter__()).returns(iter(records))

        # Processor catches ValueError and returns -1
        assert processor.sum_values() == -1
        verify().call(mock_source.__iter__()).once()

    def test_strict_return_type_validation_iter(self):
        """Test that stubbing __iter__ with a non-iterator raises TMockStubbingError."""
        mock_source = tmock(DataSource)

        # DataSource.__iter__ must return Iterator[DataRecord].
        # Passing a list directly (not an iterator) might be technically iterable but
        # stricter type checks might expect the exact return type annotation.
        # However, standard tmock validation checks if the value matches the type hint.
        # Iterator is a protocol. List matches Iterable but technically not Iterator (it doesn't have __next__).
        # Let's verify this specific strictness.

        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock_source.__iter__()).returns(123)  # Obviously wrong
        assert "Invalid return type" in str(exc.value)

    def test_iterator_side_effects(self):
        """Test using a generator function to simulate dynamic iteration logic."""
        mock_source = tmock(DataSource)
        processor = DataProcessor(mock_source)

        def dynamic_generator(args):
            yield DataRecord(1)
            yield DataRecord(2)

        # Note: .runs() expects a callable that takes 'args' and returns the value.
        # The value returned must be the iterator.
        given().call(mock_source.__iter__()).runs(lambda args: dynamic_generator(args))

        assert processor.sum_values() == 3
        verify().call(mock_source.__iter__()).once()


class TestAsyncIterationIntegration:
    @pytest.mark.asyncio
    async def test_async_processing_multiple_items(self):
        """Test standard async iteration."""
        mock_source = tmock(AsyncDataSource)
        processor = AsyncDataProcessor(mock_source)

        async def _gen():
            yield DataRecord(5)
            yield DataRecord(15)

        given().call(mock_source.__aiter__()).returns(_gen())

        result = await processor.sum_values()
        assert result == 20
        verify().call(mock_source.__aiter__()).once()

    @pytest.mark.asyncio
    async def test_async_empty_iterator(self):
        """Test empty async iterator."""
        mock_source = tmock(AsyncDataSource)
        processor = AsyncDataProcessor(mock_source)

        async def _empty():
            if False:
                yield

        given().call(mock_source.__aiter__()).returns(_empty())

        result = await processor.sum_values()
        assert result == 0
        verify().call(mock_source.__aiter__()).once()

    @pytest.mark.asyncio
    async def test_strict_return_type_validation_aiter(self):
        """Test that stubbing __aiter__ with incorrect type raises error."""
        mock_source = tmock(AsyncDataSource)

        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock_source.__aiter__()).returns("not an async iterator")
        assert "Invalid return type" in str(exc.value)

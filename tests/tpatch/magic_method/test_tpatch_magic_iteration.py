from typing import AsyncIterator, Iterator

import pytest

from tmock import given, tpatch, verify


class NumberStream:
    def __iter__(self) -> Iterator[int]:
        return iter([])


class StatefulIterator:
    def __iter__(self) -> "StatefulIterator":
        return self

    def __next__(self) -> int:
        return 0


class AsyncStream:
    def __aiter__(self) -> AsyncIterator[int]:
        async def _gen() -> AsyncIterator[int]:
            yield 0

        return _gen()


class TestPatchingIterationMagic:
    def test_iter_patching(self):
        with tpatch.method(NumberStream, "__iter__") as mock:
            data = [1, 2, 3]
            given().call(mock()).returns(iter(data))

            s = NumberStream()
            assert list(s) == [1, 2, 3]

            verify().call(mock()).once()

    def test_next_patching(self):
        with tpatch.method(StatefulIterator, "__next__") as mock:
            given().call(mock()).returns(99)

            s = StatefulIterator()
            # Note: mocking __next__ on the iterator object itself
            assert next(s) == 99

            verify().call(mock()).once()


class TestPatchingAsyncIterationMagic:
    @pytest.mark.asyncio
    async def test_aiter_patching(self):
        with tpatch.method(AsyncStream, "__aiter__") as mock:

            async def _mock_gen():
                yield 100
                yield 200

            given().call(mock()).returns(_mock_gen())

            s = AsyncStream()
            results = []
            async for x in s:
                results.append(x)

            assert results == [100, 200]
            verify().call(mock()).once()

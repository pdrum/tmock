"""Tests for patching __call__ via tpatch.method()."""

import pytest

from tmock import any, given, tpatch, verify


class CallableService:
    def __call__(self, arg: int) -> str:
        return str(arg)


class AsyncCallableService:
    async def __call__(self, arg: int) -> str:
        return f"async-{arg}"


class TestPatchingCall:
    def test_patches_call_magic_method(self) -> None:
        with tpatch.method(CallableService, "__call__") as mock:
            given().call(mock(42)).returns("mocked")

            service = CallableService()
            result = service(42)

            assert result == "mocked"
            verify().call(mock(42)).once()

    def test_verifies_call_magic_method(self) -> None:
        with tpatch.method(CallableService, "__call__") as mock:
            given().call(mock(any(int))).returns("any")

            service = CallableService()
            service(10)
            service(20)

            verify().call(mock(10)).once()
            verify().call(mock(20)).once()
            verify().call(mock(any(int))).times(2)


class TestPatchingAsyncCall:
    @pytest.mark.asyncio
    async def test_patches_async_call(self) -> None:
        with tpatch.method(AsyncCallableService, "__call__") as mock:
            given().call(mock(99)).returns("mocked-async")

            service = AsyncCallableService()
            result = await service(99)

            assert result == "mocked-async"
            verify().call(mock(99)).once()

    @pytest.mark.asyncio
    async def test_validation_on_async_call(self) -> None:
        with tpatch.method(AsyncCallableService, "__call__") as mock:
            # Should validate return type (str)
            with pytest.raises(Exception):
                given().call(mock(1)).returns(123)

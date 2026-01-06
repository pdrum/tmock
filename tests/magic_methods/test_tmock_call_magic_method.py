import pytest

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError


class CallableClass:
    def __call__(self, x: int) -> str:
        return str(x)


class AsyncCallableClass:
    async def __call__(self, x: int) -> str:
        return str(x)


class TestTMockCallMagicMethod:
    def test_stubbing_and_return(self):
        mock = tmock(CallableClass)
        given().call(mock(1)).returns("one")
        assert mock(1) == "one"

    def test_argument_type_validation(self):
        mock = tmock(CallableClass)
        # Should raise error at stubbing time due to type mismatch
        with pytest.raises(TMockStubbingError) as excinfo:
            given().call(mock("not an int")).returns("one")
        assert str(excinfo.value) == "Invalid type for argument 'x' of __call__, expected <class 'int'>, got str"

    def test_argument_matchers(self):
        mock = tmock(CallableClass)
        given().call(mock(any(int))).returns("any_int")

        assert mock(100) == "any_int"
        assert mock(200) == "any_int"

        verify().call(mock(100)).once()
        verify().call(mock(200)).once()

    def test_verification_counts(self):
        mock = tmock(CallableClass)
        given().call(mock(1)).returns("one")

        mock(1)
        mock(1)

        verify().call(mock(1)).times(2)
        verify().call(mock(1)).at_least(1)
        verify().call(mock(99)).never()

    def test_exceptions(self):
        mock = tmock(CallableClass)
        given().call(mock(0)).raises(ValueError("Zero not allowed"))

        with pytest.raises(ValueError, match="Zero not allowed"):
            mock(0)

    def test_side_effects(self):
        mock = tmock(CallableClass)
        given().call(mock(any(int))).runs(lambda args: f"processed {args.get_by_name('x')}")

        assert mock(5) == "processed 5"

    def test_unexpected_call(self):
        mock = tmock(CallableClass)
        with pytest.raises(TMockUnexpectedCallError):
            mock(99)

    def test_async_call(self):
        mock = tmock(AsyncCallableClass)

        async def run_test():
            given().call(mock(1)).returns("async_one")
            result = await mock(1)
            assert result == "async_one"
            verify().call(mock(1)).once()

        import asyncio

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(run_test())
        finally:
            loop.close()

    def test_incorrect_signature_call(self):
        mock = tmock(CallableClass)
        # Calling with too many arguments
        with pytest.raises(TMockStubbingError) as excinfo:
            given().call(mock(1, 2))
        assert "Invalid args passed to __call__" in str(excinfo.value)

    def test_return_type_validation(self):
        # NOTE: tmock currently validates return types if implemented in MethodInterceptor
        # The README says "Runtime Type Validation", let's check return type too if possible.
        # But given().call(...).returns(value) usually validates value against return annotation.

        mock = tmock(CallableClass)
        # CallableClass.__call__ returns str

        # This might not fail immediately depending on implementation,
        # but tmock usually validates return type in returns() if possible,
        # or when the stub is executed.
        # Looking at MethodInterceptor.validate_return_type usage in stubbing_dsl.py -> returns()

        with pytest.raises(TMockStubbingError) as excinfo:
            given().call(mock(1)).returns(123)  # 123 is not str
        assert "Invalid return type for __call__" in str(excinfo.value)

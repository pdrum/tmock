import pytest

from tests.patch import sample_module
from tmock import CallArguments, any, given, verify
from tmock.exceptions import TMockUnexpectedCallError
from tmock.patch import patch


class TestModuleFunctionPatching:
    def test_patch_function_with_stub(self):
        with patch(sample_module).add as mock_add:
            given().call(mock_add(1, 2)).returns(100)
            assert sample_module.add(1, 2) == 100

        # After context, original is restored
        assert sample_module.add(1, 2) == 3

    def test_patch_function_without_stub_raises(self):
        with patch(sample_module).add:
            with pytest.raises(TMockUnexpectedCallError):
                sample_module.add(1, 2)

    def test_patch_function_with_different_args(self):
        with patch(sample_module).add as mock_add:
            given().call(mock_add(1, 2)).returns(10)
            given().call(mock_add(3, 4)).returns(20)

            assert sample_module.add(1, 2) == 10
            assert sample_module.add(3, 4) == 20

    def test_patch_function_verify_calls(self):
        with patch(sample_module).greet as mock_greet:
            given().call(mock_greet("Alice")).returns("Hi!")
            given().call(mock_greet("Bob")).returns("Hey!")

            sample_module.greet("Alice")
            sample_module.greet("Bob")
            sample_module.greet("Alice")

            verify().call(mock_greet("Alice")).times(2)
            verify().call(mock_greet("Bob")).once()

    def test_patch_function_no_args(self):
        with patch(sample_module).no_args as mock_no_args:
            given().call(mock_no_args()).returns("patched")
            assert sample_module.no_args() == "patched"

        assert sample_module.no_args() == "original"

    def test_patch_nonexistent_function_raises(self):
        with pytest.raises(AttributeError) as exc_info:
            patch(sample_module).nonexistent

        assert "has no attribute 'nonexistent'" in str(exc_info.value)


class TestModuleFunctionPatchingWithMatchers:
    def test_patch_with_any_matcher(self):
        with patch(sample_module).add as mock_add:
            given().call(mock_add(any(int), any(int))).returns(999)

            assert sample_module.add(1, 2) == 999
            assert sample_module.add(100, 200) == 999

    def test_patch_with_mixed_specific_and_matcher(self):
        with patch(sample_module).add as mock_add:
            given().call(mock_add(1, any(int))).returns(100)
            given().call(mock_add(2, any(int))).returns(200)

            assert sample_module.add(1, 5) == 100
            assert sample_module.add(1, 99) == 100
            assert sample_module.add(2, 10) == 200

    def test_specific_stub_overrides_matcher(self):
        with patch(sample_module).add as mock_add:
            given().call(mock_add(any(int), any(int))).returns(0)
            given().call(mock_add(1, 2)).returns(999)

            assert sample_module.add(1, 2) == 999
            assert sample_module.add(5, 5) == 0


class TestModuleFunctionPatchingRaises:
    def test_patch_raises_exception(self):
        with patch(sample_module).divide as mock_divide:
            given().call(mock_divide(any(int), 0)).raises(ZeroDivisionError("division by zero"))

            with pytest.raises(ZeroDivisionError) as exc_info:
                sample_module.divide(10, 0)

            assert "division by zero" in str(exc_info.value)

    def test_patch_raises_custom_exception(self):
        class CustomError(Exception):
            pass

        with patch(sample_module).greet as mock_greet:
            given().call(mock_greet("error")).raises(CustomError("custom error"))

            with pytest.raises(CustomError):
                sample_module.greet("error")


class TestModuleFunctionPatchingRuns:
    def test_patch_runs_custom_action(self):
        call_log: list[tuple[int, int]] = []

        def log_and_return(args: CallArguments) -> int:
            a = args.get_by_name("a", int)
            b = args.get_by_name("b", int)
            call_log.append((a, b))
            return a * b

        with patch(sample_module).add as mock_add:
            given().call(mock_add(any(int), any(int))).runs(log_and_return)

            assert sample_module.add(3, 4) == 12
            assert sample_module.add(5, 6) == 30

        assert call_log == [(3, 4), (5, 6)]


class TestModuleFunctionPatchingDefaultArgs:
    def test_patch_function_with_default_args(self):
        with patch(sample_module).with_default as mock_fn:
            given().call(mock_fn(5, 10)).returns(100)
            given().call(mock_fn(5, 20)).returns(200)

            assert sample_module.with_default(5, 10) == 100
            assert sample_module.with_default(5, 20) == 200

    def test_patch_function_using_default_value(self):
        with patch(sample_module).with_default as mock_fn:
            # When caller uses default, y=10
            given().call(mock_fn(5, 10)).returns(999)

            assert sample_module.with_default(5) == 999


class TestModuleFunctionPatchingVerification:
    def test_verify_never_called(self):
        with patch(sample_module).add as mock_add:
            given().call(mock_add(any(int), any(int))).returns(0)
            verify().call(mock_add(1, 2)).never()

    def test_verify_at_least(self):
        with patch(sample_module).add as mock_add:
            given().call(mock_add(any(int), any(int))).returns(0)

            sample_module.add(1, 2)
            sample_module.add(1, 2)
            sample_module.add(1, 2)

            verify().call(mock_add(1, 2)).at_least(2)

    def test_verify_at_most(self):
        with patch(sample_module).add as mock_add:
            given().call(mock_add(any(int), any(int))).returns(0)

            sample_module.add(1, 2)
            sample_module.add(1, 2)

            verify().call(mock_add(1, 2)).at_most(3)

    def test_verify_called(self):
        with patch(sample_module).greet as mock_greet:
            given().call(mock_greet(any(str))).returns("hi")

            sample_module.greet("test")

            verify().call(mock_greet("test")).called()


class TestModuleFunctionPatchingAsync:
    @pytest.mark.asyncio
    async def test_patch_async_function(self):
        with patch(sample_module).async_fetch as mock_fetch:
            given().call(mock_fetch("http://example.com")).returns("mocked response")
            result = await sample_module.async_fetch("http://example.com")
            assert result == "mocked response"

        # Original restored
        result = await sample_module.async_fetch("http://example.com")
        assert result == "fetched: http://example.com"

    @pytest.mark.asyncio
    async def test_patch_async_function_with_matcher(self):
        with patch(sample_module).async_fetch as mock_fetch:
            given().call(mock_fetch(any(str))).returns("always mocked")

            result1 = await sample_module.async_fetch("http://one.com")
            result2 = await sample_module.async_fetch("http://two.com")

            assert result1 == "always mocked"
            assert result2 == "always mocked"

    @pytest.mark.asyncio
    async def test_patch_async_function_raises(self):
        with patch(sample_module).async_fetch as mock_fetch:
            given().call(mock_fetch(any(str))).raises(ConnectionError("network error"))

            with pytest.raises(ConnectionError):
                await sample_module.async_fetch("http://example.com")


class TestModuleFunctionPatchingTypeValidation:
    def test_stub_validates_argument_types(self):
        from tmock.exceptions import TMockStubbingError

        with patch(sample_module).add as mock_add:
            with pytest.raises(TMockStubbingError) as exc_info:
                given().call(mock_add("not an int", 2)).returns(0)

            assert "Invalid type for argument 'a'" in str(exc_info.value)

    def test_stub_validates_return_type(self):
        from tmock.exceptions import TMockStubbingError

        with patch(sample_module).add as mock_add:
            with pytest.raises(TMockStubbingError) as exc_info:
                given().call(mock_add(1, 2)).returns("not an int")

            assert "Invalid return type" in str(exc_info.value)

    def test_stub_validates_all_arguments(self):
        from tmock.exceptions import TMockStubbingError

        with patch(sample_module).greet as mock_greet:
            with pytest.raises(TMockStubbingError) as exc_info:
                given().call(mock_greet(123)).returns("hello")

            assert "Invalid type for argument 'name'" in str(exc_info.value)

    def test_matcher_bypasses_type_validation(self):
        # any() matcher should not trigger type validation
        with patch(sample_module).add as mock_add:
            given().call(mock_add(any(), any())).returns(999)
            assert sample_module.add(1, 2) == 999

    def test_wrong_number_of_arguments(self):
        from tmock.exceptions import TMockStubbingError

        with patch(sample_module).add as mock_add:
            with pytest.raises(TMockStubbingError) as exc_info:
                given().call(mock_add(1)).returns(0)

            assert "Invalid args" in str(exc_info.value)

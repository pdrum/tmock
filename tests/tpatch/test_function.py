import pytest

from tests.tpatch import helpers
from tests.tpatch.helpers import standalone_function
from tmock import given, tpatch, verify
from tmock.exceptions import TMockPatchingError


class TestBasicFunctionPatching:
    def test_patches_function_and_returns_stubbed_value(self) -> None:
        with tpatch.function("tests.tpatch.helpers.standalone_function") as mock:
            given().call(mock(1, "hello")).returns("mocked")

            result = helpers.standalone_function(1, "hello")

            assert result == "mocked"

    def test_restores_function_after_context_exit(self) -> None:
        with tpatch.function("tests.tpatch.helpers.standalone_function") as mock:
            given().call(mock(1, "test")).returns("mocked")
            assert helpers.standalone_function(1, "test") == "mocked"

        # After context, original is restored
        assert helpers.standalone_function(1, "test") == "test-1"

    def test_verifies_function_was_called(self) -> None:
        with tpatch.function("tests.tpatch.helpers.standalone_function") as mock:
            given().call(mock(1, "hello")).returns("mocked")

            helpers.standalone_function(1, "hello")

            verify().call(mock(1, "hello")).once()

    def test_verifies_function_call_count(self) -> None:
        with tpatch.function("tests.tpatch.helpers.standalone_function") as mock:
            given().call(mock(1, "x")).returns("mocked")

            helpers.standalone_function(1, "x")
            helpers.standalone_function(1, "x")
            helpers.standalone_function(1, "x")

            verify().call(mock(1, "x")).times(3)


class TestFunctionWithDefaults:
    def test_patches_function_with_defaults(self) -> None:
        with tpatch.function("tests.tpatch.helpers.function_with_defaults") as mock:
            given().call(mock(42)).returns("mocked-default")

            result = helpers.function_with_defaults(42)

            assert result == "mocked-default"

    def test_patches_function_with_explicit_defaults(self) -> None:
        with tpatch.function("tests.tpatch.helpers.function_with_defaults") as mock:
            given().call(mock(42, "custom", False)).returns("mocked-custom")

            result = helpers.function_with_defaults(42, "custom", False)

            assert result == "mocked-custom"


class TestAsyncFunctionPatching:
    @pytest.mark.asyncio
    async def test_patches_async_function(self) -> None:
        with tpatch.function("tests.tpatch.helpers.async_standalone_function") as mock:
            given().call(mock(5)).returns("mocked-async")

            result = await helpers.async_standalone_function(5)

            assert result == "mocked-async"

    @pytest.mark.asyncio
    async def test_restores_async_function_after_context(self) -> None:
        with tpatch.function("tests.tpatch.helpers.async_standalone_function") as mock:
            given().call(mock(5)).returns("mocked")
            assert await helpers.async_standalone_function(5) == "mocked"

        assert await helpers.async_standalone_function(5) == "async-5"

    @pytest.mark.asyncio
    async def test_verifies_async_function_calls(self) -> None:
        with tpatch.function("tests.tpatch.helpers.async_standalone_function") as mock:
            given().call(mock(10)).returns("mocked")

            await helpers.async_standalone_function(10)

            verify().call(mock(10)).once()


class TestFromImportPatching:
    def test_patches_where_imported(self) -> None:
        # This tests patching where the function is imported (in this test module)
        with tpatch.function("tests.tpatch.test_function.standalone_function") as mock:
            given().call(mock(99, "patched")).returns("from-import-works")

            # This uses the imported name directly
            result = standalone_function(99, "patched")

            assert result == "from-import-works"


class TestTypeValidation:
    def test_validates_argument_types(self) -> None:
        with tpatch.function("tests.tpatch.helpers.standalone_function") as mock:
            with pytest.raises(Exception):  # TMockStubbingError
                given().call(mock("wrong", 123))  # Types swapped

    def test_validates_return_type(self) -> None:
        with tpatch.function("tests.tpatch.helpers.standalone_function") as mock:
            with pytest.raises(Exception):  # TMockStubbingError
                given().call(mock(1, "hello")).returns(123)  # Should return str


class TestErrorHandling:
    def test_raises_on_invalid_path_format(self) -> None:
        with pytest.raises(TMockPatchingError, match="Invalid path"):
            with tpatch.function("no_dots"):
                pass

    def test_raises_on_nonexistent_module(self) -> None:
        with pytest.raises(TMockPatchingError, match="Cannot import module"):
            with tpatch.function("nonexistent.module.func"):
                pass

    def test_raises_on_nonexistent_attribute(self) -> None:
        with pytest.raises(TMockPatchingError, match="has no attribute"):
            with tpatch.function("tests.tpatch.helpers.nonexistent_function"):
                pass

    def test_raises_on_non_callable(self) -> None:
        with pytest.raises(TMockPatchingError, match="not callable"):
            with tpatch.function("tests.tpatch.helpers.MODULE_DEBUG"):
                pass


class TestMultipleStubs:
    def test_later_stubs_take_precedence(self) -> None:
        with tpatch.function("tests.tpatch.helpers.standalone_function") as mock:
            given().call(mock(1, "a")).returns("first")
            given().call(mock(1, "a")).returns("second")

            result = helpers.standalone_function(1, "a")

            assert result == "second"

    def test_different_args_have_different_stubs(self) -> None:
        with tpatch.function("tests.tpatch.helpers.standalone_function") as mock:
            given().call(mock(1, "a")).returns("one-a")
            given().call(mock(2, "b")).returns("two-b")

            assert helpers.standalone_function(1, "a") == "one-a"
            assert helpers.standalone_function(2, "b") == "two-b"

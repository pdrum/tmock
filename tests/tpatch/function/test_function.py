"""Tests for tpatch.function()."""

import pytest

from tests.tpatch.function import fixtures
from tests.tpatch.function import importer as importer_module
from tests.tpatch.function.fixtures import standalone_function
from tmock import given, tpatch, verify
from tmock.exceptions import TMockPatchingError


class TestBasicFunctionPatching:
    def test_patches_function_and_returns_stubbed_value(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.standalone_function") as mock:
            given().call(mock(1, "hello")).returns("mocked")

            result = fixtures.standalone_function(1, "hello")

            assert result == "mocked"

    def test_restores_function_after_context_exit(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.standalone_function") as mock:
            given().call(mock(1, "test")).returns("mocked")
            assert fixtures.standalone_function(1, "test") == "mocked"

        assert fixtures.standalone_function(1, "test") == "test-1"

    def test_verifies_function_was_called(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.standalone_function") as mock:
            given().call(mock(1, "hello")).returns("mocked")

            fixtures.standalone_function(1, "hello")

            verify().call(mock(1, "hello")).once()

    def test_verifies_function_call_count(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.standalone_function") as mock:
            given().call(mock(1, "x")).returns("mocked")

            fixtures.standalone_function(1, "x")
            fixtures.standalone_function(1, "x")
            fixtures.standalone_function(1, "x")

            verify().call(mock(1, "x")).times(3)


class TestFunctionWithDefaults:
    def test_patches_function_with_defaults(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.function_with_defaults") as mock:
            given().call(mock(42)).returns("mocked-default")

            result = fixtures.function_with_defaults(42)

            assert result == "mocked-default"

    def test_patches_function_with_explicit_defaults(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.function_with_defaults") as mock:
            given().call(mock(42, "custom", False)).returns("mocked-custom")

            result = fixtures.function_with_defaults(42, "custom", False)

            assert result == "mocked-custom"


class TestAsyncFunctionPatching:
    @pytest.mark.asyncio
    async def test_patches_async_function(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.async_standalone_function") as mock:
            given().call(mock(5)).returns("mocked-async")

            result = await fixtures.async_standalone_function(5)

            assert result == "mocked-async"

    @pytest.mark.asyncio
    async def test_restores_async_function_after_context(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.async_standalone_function") as mock:
            given().call(mock(5)).returns("mocked")
            assert await fixtures.async_standalone_function(5) == "mocked"

        assert await fixtures.async_standalone_function(5) == "async-5"

    @pytest.mark.asyncio
    async def test_verifies_async_function_calls(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.async_standalone_function") as mock:
            given().call(mock(10)).returns("mocked")

            await fixtures.async_standalone_function(10)

            verify().call(mock(10)).once()


class TestFromImportPatching:
    """Tests for patching functions that are imported with 'from X import Y'.

    When you do `from module import func`, you get a local binding to the function.
    To patch it, you must patch where it's imported, not where it's defined.
    """

    def test_patching_source_does_not_affect_imported_binding(self) -> None:
        """When patching the source module, the imported binding is unaffected."""
        with tpatch.function("tests.tpatch.function.fixtures.standalone_function") as mock:
            given().call(mock(1, "x")).returns("patched-at-source")

            # Source module is patched
            assert fixtures.standalone_function(1, "x") == "patched-at-source"

            # But the imported binding in importer still points to original
            result = importer_module.use_standalone_function(1, "x")
            assert result == "x-1"

    def test_patching_where_imported_works(self) -> None:
        """Patching where the function is used (after from...import) works."""
        with tpatch.function("tests.tpatch.function.importer.standalone_function") as mock:
            given().call(mock(99, "patched")).returns("from-import-works")

            result = importer_module.use_standalone_function(99, "patched")

            assert result == "from-import-works"

    def test_patching_where_imported_restores_correctly(self) -> None:
        """Patching where imported restores the original value."""
        with tpatch.function("tests.tpatch.function.importer.standalone_function") as mock:
            given().call(mock(1, "x")).returns("patched")
            assert importer_module.use_standalone_function(1, "x") == "patched"

        # After context, should be restored to original function
        assert importer_module.use_standalone_function(1, "x") == "x-1"

    def test_patching_both_source_and_importer(self) -> None:
        """Can patch both the source and where it's imported."""
        with tpatch.function("tests.tpatch.function.fixtures.standalone_function") as mock1:
            with tpatch.function("tests.tpatch.function.importer.standalone_function") as mock2:
                given().call(mock1(1, "a")).returns("source-patched")
                given().call(mock2(2, "b")).returns("importer-patched")

                assert fixtures.standalone_function(1, "a") == "source-patched"
                assert importer_module.use_standalone_function(2, "b") == "importer-patched"

    def test_local_import_in_this_module(self) -> None:
        """Test patching the locally imported function in this test module."""
        with tpatch.function("tests.tpatch.function.test_function.standalone_function") as mock:
            given().call(mock(99, "local")).returns("local-patched")

            # Uses the directly imported name at top of this file
            result = standalone_function(99, "local")

            assert result == "local-patched"


class TestTypeValidation:
    def test_validates_argument_types(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.standalone_function") as mock:
            with pytest.raises(Exception):  # TMockStubbingError
                given().call(mock("wrong", 123))  # Types swapped

    def test_validates_return_type(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.standalone_function") as mock:
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
            with tpatch.function("tests.tpatch.function.fixtures.nonexistent"):
                pass


class TestMultipleStubs:
    def test_later_stubs_take_precedence(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.standalone_function") as mock:
            given().call(mock(1, "a")).returns("first")
            given().call(mock(1, "a")).returns("second")

            result = fixtures.standalone_function(1, "a")

            assert result == "second"

    def test_different_args_have_different_stubs(self) -> None:
        with tpatch.function("tests.tpatch.function.fixtures.standalone_function") as mock:
            given().call(mock(1, "a")).returns("one-a")
            given().call(mock(2, "b")).returns("two-b")

            assert fixtures.standalone_function(1, "a") == "one-a"
            assert fixtures.standalone_function(2, "b") == "two-b"

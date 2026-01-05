"""Tests for tpatch.module_var()."""

import pytest

import tests.tpatch.module_var.fixtures as fixtures_module
import tests.tpatch.module_var.importer as importer_module
from tmock import tpatch
from tmock.exceptions import TMockPatchingError, TMockStubbingError


class TestBasicModuleVarPatching:
    def test_patches_module_var(self) -> None:
        with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_DEBUG", True):
            assert fixtures_module.MODULE_DEBUG is True

    def test_restores_module_var_after_context_exit(self) -> None:
        original = fixtures_module.MODULE_DEBUG

        with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_DEBUG", True):
            assert fixtures_module.MODULE_DEBUG is True

        assert fixtures_module.MODULE_DEBUG == original

    def test_patches_int_module_var(self) -> None:
        with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_TIMEOUT", 60):
            assert fixtures_module.MODULE_TIMEOUT == 60

    def test_patches_string_module_var(self) -> None:
        with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_NAME", "mocked"):
            assert fixtures_module.MODULE_NAME == "mocked"

    def test_context_manager_yields_nothing(self) -> None:
        with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_DEBUG", True) as result:
            assert result is None


class TestFromImportPatching:
    """Tests for patching variables that were imported via 'from ... import ...'."""

    def test_patching_source_does_not_affect_imported_binding(self) -> None:
        """When patching the source module, the imported binding is unaffected."""
        original = importer_module.MODULE_DEBUG

        with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_DEBUG", True):
            # Source module is patched
            assert fixtures_module.MODULE_DEBUG is True
            # But the imported binding in importer still has the original value
            assert importer_module.MODULE_DEBUG == original

    def test_patching_where_imported_works(self) -> None:
        """Patching where the variable is used (after from...import) works."""
        with tpatch.module_var("tests.tpatch.module_var.importer.MODULE_DEBUG", True):
            # The imported binding is now patched
            assert importer_module.MODULE_DEBUG is True

    def test_patching_where_imported_restores_correctly(self) -> None:
        """Patching where imported restores the original value."""
        original = importer_module.MODULE_DEBUG

        with tpatch.module_var("tests.tpatch.module_var.importer.MODULE_DEBUG", True):
            assert importer_module.MODULE_DEBUG is True

        assert importer_module.MODULE_DEBUG == original

    def test_patching_both_source_and_importer(self) -> None:
        """Can patch both the source and where it's imported."""
        with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_DEBUG", True):
            with tpatch.module_var("tests.tpatch.module_var.importer.MODULE_DEBUG", True):
                assert fixtures_module.MODULE_DEBUG is True
                assert importer_module.MODULE_DEBUG is True


class TestModuleVarTypeValidation:
    def test_validates_value_type(self) -> None:
        with pytest.raises(TMockStubbingError, match="Type mismatch"):
            with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_DEBUG", "not a bool"):
                pass

    def test_validates_int_type(self) -> None:
        with pytest.raises(TMockStubbingError, match="Type mismatch"):
            with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_TIMEOUT", "not an int"):
                pass

    def test_untyped_module_var_accepts_any(self) -> None:
        with tpatch.module_var("tests.tpatch.module_var.fixtures.UNTYPED_MODULE_VAR", 123):
            assert fixtures_module.UNTYPED_MODULE_VAR == 123

        with tpatch.module_var("tests.tpatch.module_var.fixtures.UNTYPED_MODULE_VAR", [1, 2, 3]):
            assert fixtures_module.UNTYPED_MODULE_VAR == [1, 2, 3]


class TestErrorHandling:
    def test_raises_on_invalid_path(self) -> None:
        with pytest.raises(TMockPatchingError, match="Invalid path"):
            with tpatch.module_var("no_dots", "value"):
                pass

    def test_raises_on_nonexistent_module(self) -> None:
        with pytest.raises(TMockPatchingError, match="Cannot import"):
            with tpatch.module_var("nonexistent.module.VAR", "value"):
                pass

    def test_raises_on_nonexistent_attribute(self) -> None:
        with pytest.raises(TMockPatchingError, match="has no attribute"):
            with tpatch.module_var("tests.tpatch.module_var.fixtures.NONEXISTENT", "value"):
                pass

    def test_raises_on_callable(self) -> None:
        with pytest.raises(TMockPatchingError, match="callable"):
            with tpatch.module_var("tests.tpatch.function.fixtures.standalone_function", "value"):
                pass


class TestMultipleModuleVars:
    def test_patches_multiple_module_vars_nested(self) -> None:
        with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_DEBUG", True):
            with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_TIMEOUT", 120):
                assert fixtures_module.MODULE_DEBUG is True
                assert fixtures_module.MODULE_TIMEOUT == 120

    def test_restores_all_module_vars_after_nested_contexts(self) -> None:
        original_debug = fixtures_module.MODULE_DEBUG
        original_timeout = fixtures_module.MODULE_TIMEOUT

        with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_DEBUG", True):
            with tpatch.module_var("tests.tpatch.module_var.fixtures.MODULE_TIMEOUT", 120):
                pass

        assert fixtures_module.MODULE_DEBUG == original_debug
        assert fixtures_module.MODULE_TIMEOUT == original_timeout

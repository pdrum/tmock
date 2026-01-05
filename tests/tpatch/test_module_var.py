import pytest

import tests.tpatch.helpers as helpers_module
from tests.tpatch.helpers import Settings
from tmock import given, tpatch, verify
from tmock.exceptions import TMockPatchingError


class TestBasicModuleVarPatching:
    def test_patches_module_var_getter(self) -> None:
        with tpatch.module_var(helpers_module, "MODULE_DEBUG") as field:
            given().get(field).returns(True)

            result = helpers_module.MODULE_DEBUG

            assert result is True

    def test_setter_stubbing_raises_error(self) -> None:
        with tpatch.module_var(helpers_module, "MODULE_DEBUG") as field:
            with pytest.raises(TMockPatchingError, match="Setter stubbing/verification is not supported"):
                given().set(field, True)

    def test_restores_module_var_after_context_exit(self) -> None:
        original = helpers_module.MODULE_DEBUG

        with tpatch.module_var(helpers_module, "MODULE_DEBUG") as field:
            given().get(field).returns(True)
            assert helpers_module.MODULE_DEBUG is True

        assert helpers_module.MODULE_DEBUG == original

    def test_patches_int_module_var(self) -> None:
        with tpatch.module_var(helpers_module, "MODULE_TIMEOUT") as field:
            given().get(field).returns(60)

            assert helpers_module.MODULE_TIMEOUT == 60

    def test_patches_string_module_var(self) -> None:
        with tpatch.module_var(helpers_module, "MODULE_NAME") as field:
            given().get(field).returns("mocked_name")

            assert helpers_module.MODULE_NAME == "mocked_name"

    def test_writes_are_discarded(self) -> None:
        original = helpers_module.MODULE_DEBUG

        with tpatch.module_var(helpers_module, "MODULE_DEBUG") as field:
            given().get(field).returns(True)

            # Write should be allowed but doesn't affect the stubbed value
            helpers_module.MODULE_DEBUG = not original

            # Should still return stubbed value
            assert helpers_module.MODULE_DEBUG is True

        # Original should be restored
        assert helpers_module.MODULE_DEBUG == original


class TestModuleVarVerification:
    """Note: Verification is limited for module variables.

    Due to Python limitations, we cannot intercept actual module attribute access.
    Verification only tracks calls made through the DSL, not direct module.VAR access.
    """

    def test_setter_verification_raises_error(self) -> None:
        with tpatch.module_var(helpers_module, "MODULE_DEBUG") as field:
            with pytest.raises(TMockPatchingError, match="Setter stubbing/verification is not supported"):
                verify().set(field, True)

    def test_verifies_getter_never_called(self) -> None:
        with tpatch.module_var(helpers_module, "MODULE_DEBUG") as field:
            given().get(field).returns(True)

            # Don't access MODULE_DEBUG

            verify().get(field).never()


class TestModuleVarTypeValidation:
    def test_validates_getter_return_type(self) -> None:
        with tpatch.module_var(helpers_module, "MODULE_DEBUG") as field:
            with pytest.raises(Exception):  # TMockStubbingError
                given().get(field).returns("not a bool")

    def test_validates_setter_value_type(self) -> None:
        with tpatch.module_var(helpers_module, "MODULE_TIMEOUT") as field:
            given().get(field).returns(0)
            with pytest.raises(TMockPatchingError, match="Setter stubbing/verification is not supported"):
                given().set(field, "not an int").returns(None)

    def test_untyped_module_var_accepts_any(self) -> None:
        with tpatch.module_var(helpers_module, "UNTYPED_MODULE_VAR") as field:
            # Should not raise - accepts any type
            given().get(field).returns(123)
            given().get(field).returns([1, 2, 3])


class TestErrorHandling:
    def test_raises_on_nonexistent_attribute(self) -> None:
        with pytest.raises(TMockPatchingError, match="has no attribute"):
            with tpatch.module_var(helpers_module, "NONEXISTENT"):
                pass

    def test_raises_on_callable(self) -> None:
        with pytest.raises(TMockPatchingError, match="callable"):
            with tpatch.module_var(helpers_module, "standalone_function"):
                pass

    def test_raises_on_non_module(self) -> None:
        with pytest.raises(TMockPatchingError, match="Expected a module"):
            with tpatch.module_var(Settings, "DEBUG"):  # type: ignore
                pass

    def test_suggests_class_var_for_class(self) -> None:
        with pytest.raises(TMockPatchingError, match="tpatch.class_var"):
            with tpatch.module_var(Settings, "DEBUG"):  # type: ignore
                pass


class TestMultipleModuleVars:
    def test_patches_multiple_module_vars_nested(self) -> None:
        with tpatch.module_var(helpers_module, "MODULE_DEBUG") as debug_field:
            with tpatch.module_var(helpers_module, "MODULE_TIMEOUT") as timeout_field:
                given().get(debug_field).returns(True)
                given().get(timeout_field).returns(120)

                assert helpers_module.MODULE_DEBUG is True
                assert helpers_module.MODULE_TIMEOUT == 120

    def test_restores_all_module_vars_after_nested_contexts(self) -> None:
        original_debug = helpers_module.MODULE_DEBUG
        original_timeout = helpers_module.MODULE_TIMEOUT

        with tpatch.module_var(helpers_module, "MODULE_DEBUG") as debug_field:
            with tpatch.module_var(helpers_module, "MODULE_TIMEOUT") as timeout_field:
                given().get(debug_field).returns(True)
                given().get(timeout_field).returns(120)

        assert helpers_module.MODULE_DEBUG == original_debug
        assert helpers_module.MODULE_TIMEOUT == original_timeout


class TestMultipleStubs:
    def test_later_stubs_take_precedence(self) -> None:
        with tpatch.module_var(helpers_module, "MODULE_DEBUG") as field:
            given().get(field).returns(False)
            given().get(field).returns(True)

            result = helpers_module.MODULE_DEBUG

            assert result is True


class TestRealWorldScenarios:
    def test_mock_config_module_variable(self) -> None:
        """Simulates mocking a config module's settings."""
        with tpatch.module_var(helpers_module, "MODULE_DEBUG") as debug:
            with tpatch.module_var(helpers_module, "MODULE_TIMEOUT") as timeout:
                given().get(debug).returns(True)
                given().get(timeout).returns(5)

                # Code under test would read these
                assert helpers_module.MODULE_DEBUG is True
                assert helpers_module.MODULE_TIMEOUT == 5

"""Tests for tpatch.class_var()."""

import re

import pytest

from tests.tpatch.class_var.fixtures import ConfigWithClassVars, Settings
from tmock import given, tpatch, verify
from tmock.exceptions import TMockPatchingError


class TestBasicClassVarPatching:
    def test_patches_class_var_getter(self) -> None:
        with tpatch.class_var(Settings, "DEBUG") as field:
            given().get(field).returns(True)

            result = Settings.DEBUG

            assert result is True

    def test_setter_stubbing_raises_error(self) -> None:
        with tpatch.class_var(Settings, "DEBUG") as field:
            with pytest.raises(TMockPatchingError, match="Setter stubbing/verification is not supported"):
                given().set(field, True)

    def test_restores_class_var_after_context_exit(self) -> None:
        original = Settings.DEBUG

        with tpatch.class_var(Settings, "DEBUG") as field:
            given().get(field).returns(True)
            assert Settings.DEBUG is True

        assert Settings.DEBUG == original

    def test_patches_typed_class_var(self) -> None:
        with tpatch.class_var(Settings, "MAX_RETRIES") as field:
            given().get(field).returns(10)

            assert Settings.MAX_RETRIES == 10

    def test_patches_string_class_var(self) -> None:
        with tpatch.class_var(Settings, "API_URL") as field:
            given().get(field).returns("https://mock.example.com")

            assert Settings.API_URL == "https://mock.example.com"

    def test_writes_are_discarded(self) -> None:
        original = Settings.DEBUG

        with tpatch.class_var(Settings, "DEBUG") as field:
            given().get(field).returns(True)

            Settings.DEBUG = not original

            assert Settings.DEBUG is True

        assert Settings.DEBUG == original


class TestClassVarVerification:
    def test_verifies_getter_called(self) -> None:
        with tpatch.class_var(Settings, "DEBUG") as field:
            given().get(field).returns(False)

            _ = Settings.DEBUG

            verify().get(field).once()

    def test_verifies_getter_call_count(self) -> None:
        with tpatch.class_var(Settings, "DEBUG") as field:
            given().get(field).returns(False)

            _ = Settings.DEBUG
            _ = Settings.DEBUG

            verify().get(field).times(2)

    def test_setter_verification_raises_error(self) -> None:
        with tpatch.class_var(Settings, "DEBUG") as field:
            with pytest.raises(TMockPatchingError, match="Setter stubbing/verification is not supported"):
                verify().set(field, True)

    def test_verifies_getter_never_called(self) -> None:
        with tpatch.class_var(Settings, "DEBUG") as field:
            given().get(field).returns(True)

            verify().get(field).never()


class TestClassVarTypeValidation:
    def test_validates_getter_return_type_from_classvar(self) -> None:
        with tpatch.class_var(Settings, "DEBUG") as field:
            with pytest.raises(Exception):  # TMockStubbingError
                given().get(field).returns("not a bool")

    def test_untyped_class_var_accepts_any(self) -> None:
        with tpatch.class_var(Settings, "UNTYPED_VAR") as field:
            given().get(field).returns(123)
            given().get(field).returns("string")
            given().get(field).returns([1, 2, 3])


class TestClassVarAccessViaInstance:
    def test_patches_class_var_accessed_via_instance(self) -> None:
        with tpatch.class_var(Settings, "DEBUG") as field:
            given().get(field).returns(True)

            settings = Settings()
            result = settings.DEBUG

            assert result is True

    def test_writes_via_instance_are_discarded(self) -> None:
        original = Settings.DEBUG

        with tpatch.class_var(Settings, "DEBUG") as field:
            given().get(field).returns(True)

            settings = Settings()
            settings.DEBUG = not original  # type: ignore[misc]

            assert settings.DEBUG is True

        assert Settings.DEBUG == original


class TestErrorHandling:
    def test_raises_on_nonexistent_attribute(self) -> None:
        with pytest.raises(TMockPatchingError, match="has no attribute"):
            with tpatch.class_var(Settings, "NONEXISTENT"):
                pass

    def test_raises_on_staticmethod(self) -> None:
        from tests.tpatch.static_method.fixtures import IdGenerator

        with pytest.raises(TMockPatchingError, match="staticmethod"):
            with tpatch.class_var(IdGenerator, "generate"):
                pass

    def test_raises_on_classmethod(self) -> None:
        from tests.tpatch.class_method.fixtures import Config

        with pytest.raises(TMockPatchingError, match="classmethod"):
            with tpatch.class_var(Config, "from_env"):
                pass

    def test_raises_on_instance_method(self) -> None:
        from tests.tpatch.method.fixtures import Calculator

        with pytest.raises(TMockPatchingError, match="callable"):
            with tpatch.class_var(Calculator, "add"):
                pass

    def test_raises_on_instance_field(self) -> None:
        from tests.tpatch.field.fixtures import Person

        with pytest.raises(TMockPatchingError, match=re.escape("Class 'Person' has no attribute 'name'.")):
            with tpatch.class_var(Person, "name"):
                pass


class TestMultipleClassVars:
    def test_patches_multiple_class_vars_nested(self) -> None:
        with tpatch.class_var(Settings, "DEBUG") as debug_field:
            with tpatch.class_var(Settings, "MAX_RETRIES") as retries_field:
                given().get(debug_field).returns(True)
                given().get(retries_field).returns(100)

                assert Settings.DEBUG is True
                assert Settings.MAX_RETRIES == 100

    def test_restores_all_class_vars_after_nested_contexts(self) -> None:
        original_debug = Settings.DEBUG
        original_retries = Settings.MAX_RETRIES

        with tpatch.class_var(Settings, "DEBUG") as debug_field:
            with tpatch.class_var(Settings, "MAX_RETRIES") as retries_field:
                given().get(debug_field).returns(True)
                given().get(retries_field).returns(100)

        assert Settings.DEBUG == original_debug
        assert Settings.MAX_RETRIES == original_retries


class TestMultipleStubs:
    def test_later_stubs_take_precedence(self) -> None:
        with tpatch.class_var(Settings, "DEBUG") as field:
            given().get(field).returns(False)
            given().get(field).returns(True)

            result = Settings.DEBUG

            assert result is True


class TestDifferentClasses:
    def test_patches_class_var_on_different_class(self) -> None:
        with tpatch.class_var(ConfigWithClassVars, "TIMEOUT") as field:
            given().get(field).returns(120)

            assert ConfigWithClassVars.TIMEOUT == 120

    def test_patches_multiple_classes(self) -> None:
        with tpatch.class_var(Settings, "DEBUG") as debug_field:
            with tpatch.class_var(ConfigWithClassVars, "ENABLED") as enabled_field:
                given().get(debug_field).returns(True)
                given().get(enabled_field).returns(False)

                assert Settings.DEBUG is True
                assert ConfigWithClassVars.ENABLED is False

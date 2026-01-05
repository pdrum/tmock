"""Tests for tpatch.static_method()."""

import pytest

from tests.tpatch.static_method.fixtures import IdGenerator
from tmock import given, tpatch, verify
from tmock.exceptions import TMockPatchingError


class TestBasicStaticMethodPatching:
    def test_patches_static_method(self) -> None:
        with tpatch.static_method(IdGenerator, "generate") as mock:
            given().call(mock()).returns("mocked-uuid")

            result = IdGenerator.generate()

            assert result == "mocked-uuid"

    def test_restores_static_method_after_context_exit(self) -> None:
        with tpatch.static_method(IdGenerator, "generate") as mock:
            given().call(mock()).returns("mocked")
            assert IdGenerator.generate() == "mocked"

        assert IdGenerator.generate() == "real-uuid"

    def test_patches_static_method_with_args(self) -> None:
        with tpatch.static_method(IdGenerator, "generate_with_prefix") as mock:
            given().call(mock("test")).returns("test-mocked-uuid")

            result = IdGenerator.generate_with_prefix("test")

            assert result == "test-mocked-uuid"

    def test_callable_on_instance(self) -> None:
        with tpatch.static_method(IdGenerator, "generate") as mock:
            given().call(mock()).returns("via-instance")

            gen = IdGenerator()
            result = gen.generate()

            assert result == "via-instance"


class TestStaticMethodVerification:
    def test_verifies_static_method_was_called(self) -> None:
        with tpatch.static_method(IdGenerator, "generate") as mock:
            given().call(mock()).returns("mocked")

            IdGenerator.generate()

            verify().call(mock()).once()

    def test_verifies_static_method_call_count(self) -> None:
        with tpatch.static_method(IdGenerator, "generate") as mock:
            given().call(mock()).returns("mocked")

            IdGenerator.generate()
            IdGenerator.generate()
            IdGenerator.generate()

            verify().call(mock()).times(3)

    def test_verifies_static_method_with_args(self) -> None:
        with tpatch.static_method(IdGenerator, "generate_with_prefix") as mock:
            given().call(mock("prefix")).returns("result")

            IdGenerator.generate_with_prefix("prefix")

            verify().call(mock("prefix")).once()


class TestAsyncStaticMethodPatching:
    @pytest.mark.asyncio
    async def test_patches_async_static_method(self) -> None:
        with tpatch.static_method(IdGenerator, "async_generate") as mock:
            given().call(mock()).returns("async-mocked")

            result = await IdGenerator.async_generate()

            assert result == "async-mocked"

    @pytest.mark.asyncio
    async def test_restores_async_static_method_after_context(self) -> None:
        with tpatch.static_method(IdGenerator, "async_generate") as mock:
            given().call(mock()).returns("mocked")
            assert await IdGenerator.async_generate() == "mocked"

        assert await IdGenerator.async_generate() == "async-real-uuid"

    @pytest.mark.asyncio
    async def test_verifies_async_static_method_calls(self) -> None:
        with tpatch.static_method(IdGenerator, "async_generate") as mock:
            given().call(mock()).returns("mocked")

            await IdGenerator.async_generate()

            verify().call(mock()).once()


class TestTypeValidation:
    def test_validates_argument_types(self) -> None:
        with tpatch.static_method(IdGenerator, "generate_with_prefix") as mock:
            with pytest.raises(Exception):  # TMockStubbingError
                given().call(mock(123))  # Should be str

    def test_validates_return_type(self) -> None:
        with tpatch.static_method(IdGenerator, "generate") as mock:
            with pytest.raises(Exception):  # TMockStubbingError
                given().call(mock()).returns(123)  # Should return str


class TestErrorHandling:
    def test_raises_on_nonexistent_method(self) -> None:
        with pytest.raises(TMockPatchingError, match="has no attribute"):
            with tpatch.static_method(IdGenerator, "nonexistent"):
                pass

    def test_raises_on_instance_method(self) -> None:
        from tests.tpatch.method.fixtures import Calculator

        with pytest.raises(TMockPatchingError, match="not a staticmethod"):
            with tpatch.static_method(Calculator, "add"):
                pass

    def test_raises_on_classmethod(self) -> None:
        from tests.tpatch.class_method.fixtures import Config

        with pytest.raises(TMockPatchingError, match="classmethod.*not a staticmethod"):
            with tpatch.static_method(Config, "from_env"):
                pass

    def test_raises_on_non_callable(self) -> None:
        from tests.tpatch.class_var.fixtures import Settings

        with pytest.raises(TMockPatchingError, match="not a staticmethod"):
            with tpatch.static_method(Settings, "DEBUG"):
                pass


class TestMultipleStubs:
    def test_later_stubs_take_precedence(self) -> None:
        with tpatch.static_method(IdGenerator, "generate") as mock:
            given().call(mock()).returns("first")
            given().call(mock()).returns("second")

            result = IdGenerator.generate()

            assert result == "second"

    def test_different_args_have_different_stubs(self) -> None:
        with tpatch.static_method(IdGenerator, "generate_with_prefix") as mock:
            given().call(mock("a")).returns("result-a")
            given().call(mock("b")).returns("result-b")

            assert IdGenerator.generate_with_prefix("a") == "result-a"
            assert IdGenerator.generate_with_prefix("b") == "result-b"

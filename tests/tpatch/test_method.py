import pytest

from tests.tpatch.helpers import Calculator, IdGenerator, ServiceWithDeps
from tmock import given, tpatch, verify
from tmock.exceptions import TMockPatchingError


class TestBasicMethodPatching:
    """Basic instance method patching tests."""

    def test_patches_instance_method(self) -> None:
        with tpatch.method(Calculator, "add") as mock:
            given().call(mock(1, 2)).returns(42)

            calc = Calculator()
            result = calc.add(1, 2)

            assert result == 42

    def test_restores_method_after_context_exit(self) -> None:
        with tpatch.method(Calculator, "add") as mock:
            given().call(mock(1, 2)).returns(42)
            assert Calculator().add(1, 2) == 42

        # Original restored
        assert Calculator().add(1, 2) == 3

    def test_patch_affects_all_instances(self) -> None:
        calc1 = Calculator()
        calc2 = Calculator()

        with tpatch.method(Calculator, "add") as mock:
            given().call(mock(5, 5)).returns(100)

            assert calc1.add(5, 5) == 100
            assert calc2.add(5, 5) == 100

    def test_patch_affects_new_instances(self) -> None:
        with tpatch.method(Calculator, "add") as mock:
            given().call(mock(1, 1)).returns(999)

            calc = Calculator()
            assert calc.add(1, 1) == 999


class TestMethodVerification:
    """Tests for method call verification."""

    def test_verifies_method_was_called(self) -> None:
        with tpatch.method(Calculator, "add") as mock:
            given().call(mock(1, 2)).returns(3)

            Calculator().add(1, 2)

            verify().call(mock(1, 2)).once()

    def test_verifies_method_call_count(self) -> None:
        with tpatch.method(Calculator, "multiply") as mock:
            given().call(mock(2, 3)).returns(6)

            calc = Calculator()
            calc.multiply(2, 3)
            calc.multiply(2, 3)

            verify().call(mock(2, 3)).times(2)

    def test_verifies_method_never_called(self) -> None:
        with tpatch.method(Calculator, "add") as mock:
            given().call(mock(1, 2)).returns(3)

            # Don't call the method

            verify().call(mock(1, 2)).never()


class TestMethodWithDefaults:
    """Tests for methods with default arguments."""

    def test_patches_method_with_defaults(self) -> None:
        with tpatch.method(Calculator, "method_with_defaults") as mock:
            given().call(mock(10)).returns("mocked-default")

            result = Calculator().method_with_defaults(10)

            assert result == "mocked-default"

    def test_patches_method_with_explicit_defaults(self) -> None:
        with tpatch.method(Calculator, "method_with_defaults") as mock:
            given().call(mock(10, "custom")).returns("mocked-custom")

            result = Calculator().method_with_defaults(10, "custom")

            assert result == "mocked-custom"


class TestAsyncMethodPatching:
    """Tests for async method patching."""

    @pytest.mark.asyncio
    async def test_patches_async_method(self) -> None:
        with tpatch.method(Calculator, "async_compute") as mock:
            given().call(mock(5)).returns(100)

            result = await Calculator().async_compute(5)

            assert result == 100

    @pytest.mark.asyncio
    async def test_restores_async_method_after_context(self) -> None:
        with tpatch.method(Calculator, "async_compute") as mock:
            given().call(mock(5)).returns(100)
            assert await Calculator().async_compute(5) == 100

        assert await Calculator().async_compute(5) == 10

    @pytest.mark.asyncio
    async def test_verifies_async_method_calls(self) -> None:
        with tpatch.method(Calculator, "async_compute") as mock:
            given().call(mock(7)).returns(14)

            await Calculator().async_compute(7)

            verify().call(mock(7)).once()


class TestTypeValidation:
    """Tests for type validation in method patching."""

    def test_validates_argument_types(self) -> None:
        with tpatch.method(Calculator, "add") as mock:
            with pytest.raises(Exception):  # TMockStubbingError
                given().call(mock("wrong", "types"))

    def test_validates_return_type(self) -> None:
        with tpatch.method(Calculator, "add") as mock:
            with pytest.raises(Exception):  # TMockStubbingError
                given().call(mock(1, 2)).returns("should be int")


class TestErrorHandling:
    """Tests for error handling."""

    def test_raises_on_nonexistent_method(self) -> None:
        with pytest.raises(TMockPatchingError, match="has no attribute"):
            with tpatch.method(Calculator, "nonexistent"):
                pass

    def test_raises_on_staticmethod(self) -> None:
        with pytest.raises(TMockPatchingError, match="staticmethod"):
            with tpatch.method(IdGenerator, "generate"):
                pass

    def test_raises_on_classmethod(self) -> None:
        from tests.tpatch.helpers import Config

        with pytest.raises(TMockPatchingError, match="classmethod"):
            with tpatch.method(Config, "from_env"):
                pass

    def test_raises_on_property(self) -> None:
        from tests.tpatch.helpers import PropertyPerson

        with pytest.raises(TMockPatchingError, match="property"):
            with tpatch.method(PropertyPerson, "name"):
                pass

    def test_raises_on_non_callable(self) -> None:
        from tests.tpatch.helpers import Settings

        with pytest.raises(TMockPatchingError, match="not callable"):
            with tpatch.method(Settings, "DEBUG"):
                pass


class TestMultipleMethods:
    """Tests for patching multiple methods."""

    def test_patches_multiple_methods_nested(self) -> None:
        with tpatch.method(Calculator, "add") as mock_add:
            with tpatch.method(Calculator, "multiply") as mock_mul:
                given().call(mock_add(1, 2)).returns(100)
                given().call(mock_mul(3, 4)).returns(200)

                calc = Calculator()
                assert calc.add(1, 2) == 100
                assert calc.multiply(3, 4) == 200

    def test_restores_all_methods_after_nested_contexts(self) -> None:
        with tpatch.method(Calculator, "add") as mock_add:
            with tpatch.method(Calculator, "multiply") as mock_mul:
                given().call(mock_add(1, 2)).returns(100)
                given().call(mock_mul(3, 4)).returns(200)

        calc = Calculator()
        assert calc.add(1, 2) == 3
        assert calc.multiply(3, 4) == 12


class TestRealWorldScenarios:
    """Tests simulating real-world usage."""

    def test_mock_external_dependency(self) -> None:
        with tpatch.method(ServiceWithDeps, "fetch_user") as mock:
            given().call(mock(123)).returns({"id": 123, "name": "Mocked User"})

            service = ServiceWithDeps()
            user = service.fetch_user(123)

            assert user == {"id": 123, "name": "Mocked User"}
            verify().call(mock(123)).once()

    def test_mock_preserves_other_methods(self) -> None:
        with tpatch.method(ServiceWithDeps, "fetch_user") as mock:
            given().call(mock(1)).returns({"id": 1, "name": "Mock"})

            service = ServiceWithDeps()

            # Patched method
            assert service.fetch_user(1) == {"id": 1, "name": "Mock"}

            # Unpatched method still works
            assert service.process("data") == "processed: data"

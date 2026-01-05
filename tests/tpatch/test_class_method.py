import pytest

from tests.tpatch.helpers import Calculator, Config, Factory, IdGenerator
from tmock import given, tpatch, verify
from tmock.exceptions import TMockPatchingError


class TestBasicClassMethodPatching:
    def test_patches_class_method(self) -> None:
        with tpatch.class_method(Config, "from_env") as mock:
            mock_config = Config()
            given().call(mock()).returns(mock_config)

            result = Config.from_env()

            assert result is mock_config

    def test_restores_class_method_after_context_exit(self) -> None:
        with tpatch.class_method(Config, "from_env") as mock:
            mock_config = Config()
            given().call(mock()).returns(mock_config)
            result = Config.from_env()
            assert result is mock_config

        # Original restored - creates new instance
        result = Config.from_env()
        assert isinstance(result, Config)

    def test_patches_class_method_with_args(self) -> None:
        with tpatch.class_method(Config, "from_dict") as mock:
            mock_config = Config()
            given().call(mock({"key": "value"})).returns(mock_config)

            result = Config.from_dict({"key": "value"})

            assert result is mock_config

    def test_callable_on_instance(self) -> None:
        with tpatch.class_method(Config, "from_env") as mock:
            mock_config = Config()
            given().call(mock()).returns(mock_config)

            config = Config()
            result = config.from_env()

            assert result is mock_config


class TestClassMethodVerification:
    def test_verifies_class_method_was_called(self) -> None:
        with tpatch.class_method(Config, "from_env") as mock:
            given().call(mock()).returns(Config())

            Config.from_env()

            verify().call(mock()).once()

    def test_verifies_class_method_call_count(self) -> None:
        with tpatch.class_method(Config, "from_env") as mock:
            given().call(mock()).returns(Config())

            Config.from_env()
            Config.from_env()

            verify().call(mock()).times(2)

    def test_verifies_class_method_with_args(self) -> None:
        with tpatch.class_method(Factory, "create") as mock:
            given().call(mock("test")).returns(Factory())

            Factory.create("test")

            verify().call(mock("test")).once()


class TestAsyncClassMethodPatching:
    @pytest.mark.asyncio
    async def test_patches_async_class_method(self) -> None:
        with tpatch.class_method(Config, "async_load") as mock:
            mock_config = Config()
            given().call(mock()).returns(mock_config)

            result = await Config.async_load()

            assert result is mock_config

    @pytest.mark.asyncio
    async def test_restores_async_class_method_after_context(self) -> None:
        with tpatch.class_method(Config, "async_load") as mock:
            mock_config = Config()
            given().call(mock()).returns(mock_config)
            result = await Config.async_load()
            assert result is mock_config

        result = await Config.async_load()
        assert isinstance(result, Config)

    @pytest.mark.asyncio
    async def test_verifies_async_class_method_calls(self) -> None:
        with tpatch.class_method(Config, "async_load") as mock:
            given().call(mock()).returns(Config())

            await Config.async_load()

            verify().call(mock()).once()


class TestTypeValidation:
    def test_validates_argument_types(self) -> None:
        with tpatch.class_method(Factory, "create") as mock:
            with pytest.raises(Exception):  # TMockStubbingError
                given().call(mock(123))  # Should be str

    def test_validates_return_type(self) -> None:
        with tpatch.class_method(Factory, "create") as mock:
            with pytest.raises(Exception):  # TMockStubbingError
                given().call(mock("test")).returns("not a Factory")


class TestErrorHandling:
    def test_raises_on_nonexistent_method(self) -> None:
        with pytest.raises(TMockPatchingError, match="has no attribute"):
            with tpatch.class_method(Config, "nonexistent"):
                pass

    def test_raises_on_instance_method(self) -> None:
        with pytest.raises(TMockPatchingError, match="not a classmethod"):
            with tpatch.class_method(Calculator, "add"):
                pass

    def test_raises_on_staticmethod(self) -> None:
        with pytest.raises(TMockPatchingError, match="staticmethod.*not a classmethod"):
            with tpatch.class_method(IdGenerator, "generate"):
                pass

    def test_raises_on_non_callable(self) -> None:
        from tests.tpatch.helpers import Settings

        with pytest.raises(TMockPatchingError, match="not a classmethod"):
            with tpatch.class_method(Settings, "DEBUG"):
                pass


class TestSubclasses:
    def test_patches_class_method_affects_subclass(self) -> None:
        class SubConfig(Config):
            pass

        with tpatch.class_method(Config, "from_env") as mock:
            mock_config = Config()
            given().call(mock()).returns(mock_config)

            # Called on parent class
            result = Config.from_env()
            assert result is mock_config

    def test_patches_subclass_class_method(self) -> None:
        class SubFactory(Factory):
            @classmethod
            def create(cls, name: str) -> "SubFactory":
                return cls()

        with tpatch.class_method(SubFactory, "create") as mock:
            mock_instance = SubFactory()
            given().call(mock("test")).returns(mock_instance)

            result = SubFactory.create("test")

            assert result is mock_instance


class TestMultipleStubs:
    def test_later_stubs_take_precedence(self) -> None:
        with tpatch.class_method(Config, "from_env") as mock:
            config1 = Config()
            config2 = Config()
            given().call(mock()).returns(config1)
            given().call(mock()).returns(config2)

            result = Config.from_env()

            assert result is config2

    def test_different_args_have_different_stubs(self) -> None:
        with tpatch.class_method(Config, "from_dict") as mock:
            config_a = Config()
            config_b = Config()
            given().call(mock({"a": 1})).returns(config_a)
            given().call(mock({"b": 2})).returns(config_b)

            assert Config.from_dict({"a": 1}) is config_a
            assert Config.from_dict({"b": 2}) is config_b

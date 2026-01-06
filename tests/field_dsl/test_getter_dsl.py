from dataclasses import dataclass
from typing import Any, NamedTuple

import pytest
from pydantic import BaseModel

from tmock import given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError, TMockVerificationError


class AnnotatedPerson:
    name: str
    age: int


@dataclass
class DataclassPerson:
    name: str
    age: int


class PropertyPerson:
    @property
    def name(self) -> str:
        return ""

    @property
    def age(self) -> int:
        return 0


class PydanticPerson(BaseModel):
    name: str
    age: int


class ExtraFieldsPerson:
    """A class with fields only defined in __init__, not discoverable by introspection."""

    def __init__(self):
        self.name = ""
        self.age = 0


class PersonConfig(NamedTuple):
    """Configuration for parameterized person class tests."""

    cls: type[Any]
    extra_fields: list[str] | None = None


PERSON_CONFIGS: list[PersonConfig] = [
    PersonConfig(AnnotatedPerson),
    PersonConfig(DataclassPerson),
    PersonConfig(PropertyPerson),
    PersonConfig(PydanticPerson),
    PersonConfig(ExtraFieldsPerson, extra_fields=["name", "age"]),
]


def config_name(config: PersonConfig) -> str:
    return config.cls.__name__


class TestGetterStubbing:
    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_stub_getter_returns_value(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        assert mock.name == "Alice"

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_stub_multiple_getters(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Bob")
        given().get(mock.age).returns(30)

        assert mock.name == "Bob"
        assert mock.age == 30

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_unstubbed_getter_raises(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)

        with pytest.raises(TMockUnexpectedCallError):
            _ = mock.name

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_stub_getter_with_different_return_types(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Test")

        result = mock.name
        assert isinstance(result, str)
        assert result == "Test"

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_stub_getter_can_be_called_multiple_times(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        assert mock.name == "Alice"
        assert mock.name == "Alice"
        assert mock.name == "Alice"

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_later_stub_overrides_earlier(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("First")
        given().get(mock.name).returns("Second")

        assert mock.name == "Second"

    def test_stub_getter_with_none_value(self):
        class OptionalPerson:
            nickname: str | None

        mock = tmock(OptionalPerson)
        given().get(mock.nickname).returns(None)

        assert mock.nickname is None


class TestGetterVerification:
    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_getter_called_once(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        _ = mock.name

        verify().get(mock.name).once()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_getter_called_multiple_times(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        _ = mock.name
        _ = mock.name
        _ = mock.name

        verify().get(mock.name).times(3)

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_getter_never_called(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        verify().get(mock.name).never()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_getter_fails_when_not_called(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        with pytest.raises(TMockVerificationError):
            verify().get(mock.name).once()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_getter_fails_with_wrong_count(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        _ = mock.name
        _ = mock.name

        with pytest.raises(TMockVerificationError):
            verify().get(mock.name).once()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_different_getters_independently(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")
        given().get(mock.age).returns(25)

        _ = mock.name
        _ = mock.name
        _ = mock.age

        verify().get(mock.name).times(2)
        verify().get(mock.age).once()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_getter_called(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        _ = mock.name

        verify().get(mock.name).called()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_getter_at_least(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        _ = mock.name
        _ = mock.name
        _ = mock.name

        verify().get(mock.name).at_least(2)

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_getter_at_most(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        _ = mock.name

        verify().get(mock.name).at_most(2)

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_getter_at_least_fails(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        _ = mock.name

        with pytest.raises(TMockVerificationError):
            verify().get(mock.name).at_least(3)

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_getter_at_most_fails(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        _ = mock.name
        _ = mock.name
        _ = mock.name

        with pytest.raises(TMockVerificationError):
            verify().get(mock.name).at_most(2)


class TestGetterValidation:
    def test_get_rejects_non_field_ref(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            given().get("not a field ref").returns("value")

        assert "get() expects a field access" in str(exc_info.value)

    def test_get_rejects_none(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            given().get(None).returns("value")

        assert "get() expects a field access" in str(exc_info.value)

    def test_get_rejects_integer(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            given().get(42).returns("value")

        assert "get() expects a field access" in str(exc_info.value)

    def test_get_rejects_list(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            given().get([1, 2, 3]).returns("value")

        assert "get() expects a field access" in str(exc_info.value)

    def test_get_rejects_method_call_result(self):
        class Calculator:
            def add(self, a: int, b: int) -> int:
                return a + b

        mock = tmock(Calculator)
        given().call(mock.add(1, 2)).returns(3)

        with pytest.raises(TMockStubbingError) as exc_info:
            given().get(mock.add(1, 2)).returns("value")

        assert "get() expects a field access" in str(exc_info.value)

    def test_verify_get_rejects_non_field_ref(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            verify().get("not a field ref").once()

        assert "get() expects a field access" in str(exc_info.value)

    def test_verify_get_rejects_none(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            verify().get(None).once()

        assert "get() expects a field access" in str(exc_info.value)


class TestGetterTypeValidation:
    @pytest.mark.parametrize(
        "config",
        [c for c in PERSON_CONFIGS if c.extra_fields is None],
        ids=config_name,
    )
    def test_getter_returns_wrong_type_raises(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)

        with pytest.raises(TMockStubbingError):
            given().get(mock.name).returns(123)  # name is str, not int

    @pytest.mark.parametrize(
        "config",
        [c for c in PERSON_CONFIGS if c.extra_fields is None],
        ids=config_name,
    )
    def test_getter_returns_wrong_type_for_int_field(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)

        with pytest.raises(TMockStubbingError):
            given().get(mock.age).returns("not an int")  # age is int, not str

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_getter_returns_correct_type_passes(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("valid string")
        given().get(mock.age).returns(42)

        assert mock.name == "valid string"
        assert mock.age == 42


class TestGetterEdgeCases:
    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_getter_stubbing_does_not_count_as_call(self, config):
        mock = tmock(config.cls, extra_fields=config.extra_fields)
        given().get(mock.name).returns("Alice")

        verify().get(mock.name).never()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_multiple_mocks_have_independent_getters(self, config):
        mock1 = tmock(config.cls, extra_fields=config.extra_fields)
        mock2 = tmock(config.cls, extra_fields=config.extra_fields)

        given().get(mock1.name).returns("Alice")
        given().get(mock2.name).returns("Bob")

        assert mock1.name == "Alice"
        assert mock2.name == "Bob"

        verify().get(mock1.name).once()
        verify().get(mock2.name).once()

    def test_getter_with_complex_type(self):
        class Container:
            items: list[str]

        mock = tmock(Container)
        given().get(mock.items).returns(["a", "b", "c"])

        assert mock.items == ["a", "b", "c"]


class TestExtraFieldsPriority:
    def test_typed_field_takes_priority_over_extra_field(self):
        """Typed annotations should be used even if the field is also in extra_fields."""

        class TypedPerson:
            name: str

        # Even though we pass name as extra_field, the typed annotation should take priority
        mock = tmock(TypedPerson, extra_fields=["name"])
        given().get(mock.name).returns("Alice")

        assert mock.name == "Alice"

        # The field should still have type checking from the annotation
        with pytest.raises(TMockStubbingError):
            given().get(mock.name).returns(123)  # Should fail type check

    def test_extra_field_used_when_no_annotation_exists(self):
        """Extra fields should be used for fields not discoverable by introspection."""

        class UntypedPerson:
            def __init__(self):
                self.name = ""

        mock = tmock(UntypedPerson, extra_fields=["name"])
        # Extra fields have Any type, so any value should work
        given().get(mock.name).returns("Alice")
        assert mock.name == "Alice"

        given().get(mock.name).returns(123)  # Should not raise - Any type
        assert mock.name == 123

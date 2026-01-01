from dataclasses import dataclass
from typing import Any, NamedTuple

import pytest
from pydantic import BaseModel

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError, TMockVerificationError


class AnnotatedPerson:
    name: str
    age: int


@dataclass
class DataclassPerson:
    name: str
    age: int


class PropertyPerson:
    _name: str = ""
    _age: int = 0

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        self._age = value


class PydanticPerson(BaseModel):
    model_config = {"frozen": False}
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


class TestSetterStubbing:
    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_stub_setter_allows_assignment(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, "Alice").returns(None)

        mock.name = "Alice"  # Should not raise

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_stub_setter_with_any_matcher(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"
        mock.name = "Bob"
        mock.name = "Charlie"

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_unstubbed_setter_raises(self, config):
        mock = tmock(config.cls, config.extra_fields)

        with pytest.raises(TMockUnexpectedCallError):
            mock.name = "Alice"

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_setter_with_wrong_value_raises(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, "Alice").returns(None)

        with pytest.raises(TMockUnexpectedCallError):
            mock.name = "Bob"

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_stub_multiple_setters(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)
        given().set(mock.age, any(int)).returns(None)

        mock.name = "Alice"
        mock.age = 30

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_stub_setter_with_specific_values(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, "Alice").returns(None)
        given().set(mock.name, "Bob").returns(None)

        mock.name = "Alice"
        mock.name = "Bob"

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_later_stub_overrides_earlier_for_same_value(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, "Alice").returns(None)
        given().set(mock.name, "Alice").returns(None)  # Duplicate stub is fine

        mock.name = "Alice"

    def test_stub_setter_with_none_value(self):
        class OptionalPerson:
            nickname: str | None

        mock = tmock(OptionalPerson)
        given().set(mock.nickname, None).returns(None)

        mock.nickname = None  # Should not raise


class TestSetterVerification:
    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_setter_called_once(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"

        verify().set(mock.name, "Alice").once()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_setter_called_multiple_times(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"
        mock.name = "Alice"
        mock.name = "Alice"

        verify().set(mock.name, "Alice").times(3)

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_setter_with_any_matcher(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"
        mock.name = "Bob"

        verify().set(mock.name, any(str)).times(2)

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_setter_never_called(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        verify().set(mock.name, "Alice").never()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_setter_fails_when_not_called(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        with pytest.raises(TMockVerificationError):
            verify().set(mock.name, "Alice").once()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_setter_with_specific_value(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"
        mock.name = "Bob"
        mock.name = "Alice"

        verify().set(mock.name, "Alice").times(2)
        verify().set(mock.name, "Bob").once()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_setter_called(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"

        verify().set(mock.name, "Alice").called()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_setter_at_least(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"
        mock.name = "Alice"
        mock.name = "Alice"

        verify().set(mock.name, any(str)).at_least(2)

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_setter_at_most(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"

        verify().set(mock.name, any(str)).at_most(2)

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_setter_at_least_fails(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"

        with pytest.raises(TMockVerificationError):
            verify().set(mock.name, any(str)).at_least(3)

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_verify_setter_at_most_fails(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"
        mock.name = "Alice"
        mock.name = "Alice"

        with pytest.raises(TMockVerificationError):
            verify().set(mock.name, any(str)).at_most(2)


class TestSetterValidation:
    def test_set_rejects_non_field_ref(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            given().set("not a field ref", "value").returns(None)

        assert "set() expects a field access" in str(exc_info.value)

    def test_set_rejects_none(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            given().set(None, "value").returns(None)

        assert "set() expects a field access" in str(exc_info.value)

    def test_set_rejects_integer(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            given().set(42, "value").returns(None)

        assert "set() expects a field access" in str(exc_info.value)

    def test_set_rejects_list(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            given().set([1, 2, 3], "value").returns(None)

        assert "set() expects a field access" in str(exc_info.value)

    def test_set_rejects_method_call_result(self):
        class Calculator:
            def add(self, a: int, b: int) -> int:
                return a + b

        mock = tmock(Calculator)
        given().call(mock.add(1, 2)).returns(3)

        with pytest.raises(TMockStubbingError) as exc_info:
            given().set(mock.add(1, 2), "value").returns(None)

        assert "set() expects a field access" in str(exc_info.value)

    def test_verify_set_rejects_non_field_ref(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            verify().set("not a field ref", "value").once()

        assert "set() expects a field access" in str(exc_info.value)

    def test_verify_set_rejects_none(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            verify().set(None, "value").once()

        assert "set() expects a field access" in str(exc_info.value)


class TestSetterTypeValidation:
    @pytest.mark.parametrize(
        "config",
        [c for c in PERSON_CONFIGS if c.extra_fields is None],
        ids=config_name,
    )
    def test_setter_with_wrong_type_value_raises(self, config):
        mock = tmock(config.cls, config.extra_fields)

        with pytest.raises(TMockStubbingError):
            given().set(mock.name, 123).returns(None)  # name is str, not int

    @pytest.mark.parametrize(
        "config",
        [c for c in PERSON_CONFIGS if c.extra_fields is None],
        ids=config_name,
    )
    def test_setter_with_wrong_type_for_int_field(self, config):
        mock = tmock(config.cls, config.extra_fields)

        with pytest.raises(TMockStubbingError):
            given().set(mock.age, "not an int").returns(None)  # age is int, not str

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_setter_with_correct_type_passes(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, "valid string").returns(None)
        given().set(mock.age, 42).returns(None)

        mock.name = "valid string"
        mock.age = 42


class TestSetterReturnsValidation:
    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_setter_returns_non_none_raises(self, config):
        mock = tmock(config.cls, config.extra_fields)

        with pytest.raises(TMockStubbingError):
            given().set(mock.name, "Alice").returns("should be None")

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_setter_returns_integer_raises(self, config):
        mock = tmock(config.cls, config.extra_fields)

        with pytest.raises(TMockStubbingError):
            given().set(mock.name, "Alice").returns(42)

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_setter_returns_none_passes(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, "Alice").returns(None)

        mock.name = "Alice"  # Should not raise


class TestReadOnlyField:
    def test_set_rejects_readonly_property(self):
        class Sample:
            @property
            def readonly(self) -> str:
                return "constant"

        mock = tmock(Sample)

        with pytest.raises(TMockStubbingError) as exc_info:
            given().set(mock.readonly, "new value").returns(None)

        assert "read-only" in str(exc_info.value)

    def test_verify_set_rejects_readonly_property(self):
        class Sample:
            @property
            def readonly(self) -> str:
                return "constant"

        mock = tmock(Sample)

        with pytest.raises(TMockStubbingError) as exc_info:
            verify().set(mock.readonly, "value").once()

        assert "read-only" in str(exc_info.value)

    def test_frozen_dataclass_field_is_readonly(self):
        @dataclass(frozen=True)
        class FrozenUser:
            name: str

        mock = tmock(FrozenUser)

        with pytest.raises(TMockStubbingError) as exc_info:
            given().set(mock.name, "new name").returns(None)

        assert "read-only" in str(exc_info.value)

    def test_frozen_pydantic_field_is_readonly(self):
        class FrozenPydanticUser(BaseModel):
            model_config = {"frozen": True}
            name: str

        mock = tmock(FrozenPydanticUser)

        with pytest.raises(TMockStubbingError) as exc_info:
            given().set(mock.name, "new name").returns(None)

        assert "read-only" in str(exc_info.value)


class TestSetterEdgeCases:
    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_setter_stubbing_does_not_count_as_call(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().set(mock.name, any(str)).returns(None)

        # Stubbing should not count as a call
        verify().set(mock.name, any(str)).never()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_multiple_mocks_have_independent_setters(self, config):
        mock1 = tmock(config.cls, config.extra_fields)
        mock2 = tmock(config.cls, config.extra_fields)

        given().set(mock1.name, any(str)).returns(None)
        given().set(mock2.name, any(str)).returns(None)

        mock1.name = "Alice"
        mock2.name = "Bob"

        verify().set(mock1.name, "Alice").once()
        verify().set(mock2.name, "Bob").once()

    @pytest.mark.parametrize("config", PERSON_CONFIGS, ids=config_name)
    def test_getter_and_setter_are_independent(self, config):
        mock = tmock(config.cls, config.extra_fields)
        given().get(mock.name).returns("Alice")
        given().set(mock.name, any(str)).returns(None)

        # Get the value
        assert mock.name == "Alice"

        # Set a new value
        mock.name = "Bob"

        # Verify independently
        verify().get(mock.name).once()
        verify().set(mock.name, "Bob").once()

    def test_setter_with_complex_type(self):
        class Container:
            items: list[str]

        mock = tmock(Container)
        given().set(mock.items, any(list)).returns(None)

        mock.items = ["a", "b", "c"]

        verify().set(mock.items, ["a", "b", "c"]).once()


class TestExtraFieldsPriority:
    def test_typed_field_takes_priority_over_extra_field(self):
        """Typed annotations should be used even if the field is also in extra_fields."""

        class TypedPerson:
            name: str

        # Even though we pass name as extra_field, the typed annotation should take priority
        mock = tmock(TypedPerson, extra_fields=["name"])
        given().set(mock.name, "Alice").returns(None)

        mock.name = "Alice"

        # The field should still have type checking from the annotation
        with pytest.raises(TMockStubbingError):
            given().set(mock.name, 123).returns(None)  # Should fail type check

    def test_extra_field_used_when_no_annotation_exists(self):
        """Extra fields should be used for fields not discoverable by introspection."""

        class UntypedPerson:
            def __init__(self):
                self.name = ""

        mock = tmock(UntypedPerson, extra_fields=["name"])
        # Extra fields have Any type, so any value should work
        given().set(mock.name, "Alice").returns(None)
        mock.name = "Alice"

        given().set(mock.name, 123).returns(None)  # Should not raise - Any type
        mock.name = 123

from dataclasses import dataclass
from typing import Any

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


PERSON_CLASSES: list[type[Any]] = [AnnotatedPerson, DataclassPerson, PropertyPerson, PydanticPerson]


def class_name(cls: type[Any]) -> str:
    return cls.__name__


class TestGetterStubbing:
    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_stub_getter_returns_value(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        assert mock.name == "Alice"

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_stub_multiple_getters(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Bob")
        given().get(mock.age).returns(30)

        assert mock.name == "Bob"
        assert mock.age == 30

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_unstubbed_getter_raises(self, person_cls):
        mock = tmock(person_cls)

        with pytest.raises(TMockUnexpectedCallError):
            _ = mock.name

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_stub_getter_with_different_return_types(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Test")

        result = mock.name
        assert isinstance(result, str)
        assert result == "Test"

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_stub_getter_can_be_called_multiple_times(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        assert mock.name == "Alice"
        assert mock.name == "Alice"
        assert mock.name == "Alice"

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_later_stub_overrides_earlier(self, person_cls):
        mock = tmock(person_cls)
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
    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_verify_getter_called_once(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        _ = mock.name

        verify().get(mock.name).once()

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_verify_getter_called_multiple_times(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        _ = mock.name
        _ = mock.name
        _ = mock.name

        verify().get(mock.name).times(3)

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_verify_getter_never_called(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        verify().get(mock.name).never()

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_verify_getter_fails_when_not_called(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        with pytest.raises(TMockVerificationError):
            verify().get(mock.name).once()

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_verify_getter_fails_with_wrong_count(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        _ = mock.name
        _ = mock.name

        with pytest.raises(TMockVerificationError):
            verify().get(mock.name).once()

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_verify_different_getters_independently(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")
        given().get(mock.age).returns(25)

        _ = mock.name
        _ = mock.name
        _ = mock.age

        verify().get(mock.name).times(2)
        verify().get(mock.age).once()

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_verify_getter_called(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        _ = mock.name

        verify().get(mock.name).called()

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_verify_getter_at_least(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        _ = mock.name
        _ = mock.name
        _ = mock.name

        verify().get(mock.name).at_least(2)

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_verify_getter_at_most(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        _ = mock.name

        verify().get(mock.name).at_most(2)

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_verify_getter_at_least_fails(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        _ = mock.name

        with pytest.raises(TMockVerificationError):
            verify().get(mock.name).at_least(3)

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_verify_getter_at_most_fails(self, person_cls):
        mock = tmock(person_cls)
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
    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_getter_returns_wrong_type_raises(self, person_cls):
        mock = tmock(person_cls)

        with pytest.raises(TMockStubbingError):
            given().get(mock.name).returns(123)  # name is str, not int

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_getter_returns_wrong_type_for_int_field(self, person_cls):
        mock = tmock(person_cls)

        with pytest.raises(TMockStubbingError):
            given().get(mock.age).returns("not an int")  # age is int, not str

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_getter_returns_correct_type_passes(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("valid string")
        given().get(mock.age).returns(42)

        assert mock.name == "valid string"
        assert mock.age == 42


class TestGetterEdgeCases:
    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_getter_stubbing_does_not_count_as_call(self, person_cls):
        mock = tmock(person_cls)
        given().get(mock.name).returns("Alice")

        verify().get(mock.name).never()

    @pytest.mark.parametrize("person_cls", PERSON_CLASSES, ids=class_name)
    def test_multiple_mocks_have_independent_getters(self, person_cls):
        mock1 = tmock(person_cls)
        mock2 = tmock(person_cls)

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

import pytest

from tests.tpatch.helpers import (
    AnnotatedFields,
    Calculator,
    FrozenPydanticUser,
    ImmutablePerson,
    Person,
    PropertyPerson,
    PydanticUser,
    Settings,
)
from tmock import given, tpatch, verify
from tmock.exceptions import TMockPatchingError


class TestDataclassFieldPatching:
    def test_patches_dataclass_getter(self) -> None:
        with tpatch.field(Person, "name") as field:
            given().get(field).returns("Mocked Name")

            person = Person.__new__(Person)
            result = person.name

            assert result == "Mocked Name"

    def test_patches_dataclass_setter(self) -> None:
        with tpatch.field(Person, "name") as field:
            given().get(field).returns("Initial")
            given().set(field, "New Name").returns(None)

            person = Person.__new__(Person)
            person.name = "New Name"

            verify().set(field, "New Name").once()

    def test_restores_dataclass_field_after_context(self) -> None:
        with tpatch.field(Person, "name") as field:
            given().get(field).returns("Mocked")
            person = Person.__new__(Person)
            assert person.name == "Mocked"

        # Original behavior restored
        person = Person(name="Real", age=30)
        assert person.name == "Real"

    def test_frozen_dataclass_has_no_setter(self) -> None:
        with tpatch.field(ImmutablePerson, "name") as field:
            given().get(field).returns("Mocked")

            person = ImmutablePerson.__new__(ImmutablePerson)

            # Getter works
            assert person.name == "Mocked"

            # Setter should raise (FrozenInstanceError from dataclass or TMockPatchingError)
            with pytest.raises(Exception):
                person.name = "New"  # type: ignore[misc]


class TestPropertyFieldPatching:
    """Tests for property field patching."""

    def test_patches_property_getter(self) -> None:
        with tpatch.field(PropertyPerson, "name") as field:
            given().get(field).returns("Mocked Property")

            person = PropertyPerson()
            result = person.name

            assert result == "Mocked Property"

    def test_patches_property_setter(self) -> None:
        with tpatch.field(PropertyPerson, "name") as field:
            given().get(field).returns("Initial")
            given().set(field, "Updated").returns(None)

            person = PropertyPerson()
            person.name = "Updated"

            verify().set(field, "Updated").once()

    def test_read_only_property_has_no_setter(self) -> None:
        with tpatch.field(PropertyPerson, "read_only_prop") as field:
            given().get(field).returns("Mocked Read Only")

            person = PropertyPerson()
            assert person.read_only_prop == "Mocked Read Only"

            with pytest.raises(TMockPatchingError, match="read-only"):
                person.read_only_prop = "Attempt"  # type: ignore[misc]

    def test_restores_property_after_context(self) -> None:
        with tpatch.field(PropertyPerson, "name") as field:
            given().get(field).returns("Mocked")

        person = PropertyPerson()
        assert person.name == "default"


class TestAnnotatedFieldPatching:
    """Tests for annotated field patching."""

    def test_patches_annotated_field_getter(self) -> None:
        with tpatch.field(AnnotatedFields, "name") as field:
            given().get(field).returns("Annotated Mocked")

            obj = AnnotatedFields.__new__(AnnotatedFields)
            result = obj.name

            assert result == "Annotated Mocked"

    def test_patches_annotated_field_setter(self) -> None:
        with tpatch.field(AnnotatedFields, "count") as field:
            given().get(field).returns(0)
            given().set(field, 42).returns(None)

            obj = AnnotatedFields.__new__(AnnotatedFields)
            obj.count = 42

            verify().set(field, 42).once()


class TestPydanticFieldPatching:
    """Tests for Pydantic model field patching."""

    def test_patches_pydantic_getter(self) -> None:
        with tpatch.field(PydanticUser, "name") as field:
            given().get(field).returns("Pydantic Mocked")

            user = PydanticUser.__new__(PydanticUser)
            result = user.name

            assert result == "Pydantic Mocked"

    def test_patches_pydantic_setter_raises_without_init(self) -> None:
        # Note: Pydantic's __setattr__ requires proper initialization.
        # Using __new__ bypasses Pydantic's __init__, so setters raise errors.
        with tpatch.field(PydanticUser, "email") as field:
            given().get(field).returns("old@example.com")
            given().set(field, "new@example.com").returns(None)

            user = PydanticUser.__new__(PydanticUser)

            # Raises because Pydantic model isn't properly initialized
            with pytest.raises(AttributeError):
                user.email = "new@example.com"

    def test_frozen_pydantic_has_no_setter(self) -> None:
        with tpatch.field(FrozenPydanticUser, "name") as field:
            given().get(field).returns("Frozen Mocked")

            user = FrozenPydanticUser.__new__(FrozenPydanticUser)
            assert user.name == "Frozen Mocked"

            # Setter should raise (ValidationError from Pydantic or TMockPatchingError)
            with pytest.raises(Exception):
                user.name = "Attempt"


class TestFieldVerification:
    """Tests for field access verification."""

    def test_verifies_getter_called(self) -> None:
        with tpatch.field(Person, "name") as field:
            given().get(field).returns("Name")

            person = Person.__new__(Person)
            _ = person.name

            verify().get(field).once()

    def test_verifies_getter_call_count(self) -> None:
        with tpatch.field(Person, "age") as field:
            given().get(field).returns(25)

            person = Person.__new__(Person)
            _ = person.age
            _ = person.age
            _ = person.age

            verify().get(field).times(3)

    def test_verifies_setter_called(self) -> None:
        with tpatch.field(Person, "name") as field:
            given().get(field).returns("Initial")
            given().set(field, "New").returns(None)

            person = Person.__new__(Person)
            person.name = "New"

            verify().set(field, "New").once()

    def test_verifies_getter_never_called(self) -> None:
        with tpatch.field(Person, "name") as field:
            given().get(field).returns("Name")

            # Don't access the field

            verify().get(field).never()


class TestTypeValidation:
    """Tests for type validation in field patching."""

    def test_validates_getter_return_type(self) -> None:
        with tpatch.field(Person, "name") as field:
            with pytest.raises(Exception):  # TMockStubbingError
                given().get(field).returns(123)  # Should be str

    def test_validates_setter_value_type(self) -> None:
        with tpatch.field(Person, "age") as field:
            given().get(field).returns(0)
            with pytest.raises(Exception):  # TMockStubbingError
                given().set(field, "not an int").returns(None)


class TestErrorHandling:
    """Tests for error handling."""

    def test_raises_on_nonexistent_field(self) -> None:
        with pytest.raises(TMockPatchingError, match="not a field"):
            with tpatch.field(Person, "nonexistent"):
                pass

    def test_raises_on_method(self) -> None:
        with pytest.raises(TMockPatchingError, match="not a field"):
            with tpatch.field(Calculator, "add"):
                pass

    def test_raises_on_class_variable(self) -> None:
        with pytest.raises(TMockPatchingError, match="class_var"):
            with tpatch.field(Settings, "DEBUG"):
                pass

    def test_suggests_class_var_for_class_variables(self) -> None:
        with pytest.raises(TMockPatchingError, match="tpatch.class_var"):
            with tpatch.field(Settings, "MAX_RETRIES"):
                pass


class TestMultipleFields:
    """Tests for patching multiple fields."""

    def test_patches_multiple_fields_nested(self) -> None:
        with tpatch.field(Person, "name") as name_field:
            with tpatch.field(Person, "age") as age_field:
                given().get(name_field).returns("Alice")
                given().get(age_field).returns(30)

                person = Person.__new__(Person)
                assert person.name == "Alice"
                assert person.age == 30

    def test_restores_all_fields_after_nested_contexts(self) -> None:
        with tpatch.field(Person, "name") as name_field:
            with tpatch.field(Person, "age") as age_field:
                given().get(name_field).returns("Mocked")
                given().get(age_field).returns(99)

        person = Person(name="Real", age=25)
        assert person.name == "Real"
        assert person.age == 25


class TestFieldAffectsAllInstances:
    """Tests verifying patches affect all instances."""

    def test_patch_affects_existing_instances(self) -> None:
        person1 = PropertyPerson()
        person2 = PropertyPerson()

        with tpatch.field(PropertyPerson, "name") as field:
            given().get(field).returns("Shared Mock")

            assert person1.name == "Shared Mock"
            assert person2.name == "Shared Mock"

    def test_patch_affects_new_instances(self) -> None:
        with tpatch.field(PropertyPerson, "name") as field:
            given().get(field).returns("New Instance Mock")

            person = PropertyPerson()
            assert person.name == "New Instance Mock"

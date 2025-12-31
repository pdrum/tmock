from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

from tmock.class_schema import FieldSource, introspect_class


class TestPydanticDiscovery:
    def test_discovers_pydantic_fields(self):
        class Sample(BaseModel):
            name: str
            count: int

        schema = introspect_class(Sample)

        assert "name" in schema.fields
        assert "count" in schema.fields
        assert schema.fields["name"].source == FieldSource.PYDANTIC
        assert schema.fields["count"].source == FieldSource.PYDANTIC

    def test_getter_signature_has_correct_return_type(self):
        class Sample(BaseModel):
            value: int

        schema = introspect_class(Sample)
        field_schema = schema.fields["value"]

        assert field_schema.getter_signature.return_annotation is int

    def test_mutable_model_has_setters(self):
        class Sample(BaseModel):
            name: str

        schema = introspect_class(Sample)
        field_schema = schema.fields["name"]

        assert field_schema.setter_signature is not None
        params = list(field_schema.setter_signature.parameters.values())
        assert len(params) == 1
        assert params[0].name == "value"
        assert params[0].annotation is str

    def test_frozen_model_has_no_setters(self):
        class Sample(BaseModel):
            model_config = ConfigDict(frozen=True)
            name: str
            count: int

        schema = introspect_class(Sample)

        assert schema.fields["name"].setter_signature is None
        assert schema.fields["count"].setter_signature is None

    def test_field_with_default(self):
        class Sample(BaseModel):
            name: str = "default"
            count: int = Field(default=0)

        schema = introspect_class(Sample)

        assert "name" in schema.fields
        assert "count" in schema.fields

    def test_field_with_default_factory(self):
        class Sample(BaseModel):
            items: list[str] = Field(default_factory=list)

        schema = introspect_class(Sample)

        assert "items" in schema.fields
        field_schema = schema.fields["items"]
        assert field_schema.getter_signature.return_annotation == list[str]

    def test_optional_field(self):
        class Sample(BaseModel):
            maybe_name: Optional[str] = None

        schema = introspect_class(Sample)

        assert "maybe_name" in schema.fields
        field_schema = schema.fields["maybe_name"]
        assert field_schema.getter_signature.return_annotation == Optional[str]

    def test_skips_private_fields(self):
        class Sample(BaseModel):
            public: str
            _private: str = "secret"

        schema = introspect_class(Sample)

        assert "public" in schema.fields
        assert "_private" not in schema.fields

    def test_inherited_model(self):
        class Base(BaseModel):
            base_field: str

        class Child(Base):
            child_field: int

        schema = introspect_class(Child)

        assert "base_field" in schema.fields
        assert "child_field" in schema.fields
        assert schema.fields["base_field"].source == FieldSource.PYDANTIC
        assert schema.fields["child_field"].source == FieldSource.PYDANTIC

    def test_computed_field_discovered_as_property(self):
        class Sample(BaseModel):
            first_name: str
            last_name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

        schema = introspect_class(Sample)

        # Computed fields are properties, so they get discovered as PROPERTY
        # (properties are discovered before pydantic in the merge order)
        assert "full_name" in schema.fields
        assert schema.fields["full_name"].source == FieldSource.PROPERTY

    def test_model_fields_not_in_methods(self):
        class Sample(BaseModel):
            value: int

            def get_value(self) -> int:
                return self.value

        schema = introspect_class(Sample)

        assert "value" in schema.fields
        assert "value" not in schema.method_signatures
        assert "get_value" in schema.method_signatures

    def test_non_pydantic_class_returns_no_pydantic_fields(self):
        class NotAPydanticModel:
            name: str

        schema = introspect_class(NotAPydanticModel)

        # Should still discover via annotations
        assert "name" in schema.fields
        assert schema.fields["name"].source == FieldSource.ANNOTATION


class TestPydanticPrecedence:
    def test_pydantic_takes_precedence_over_dataclass_annotation(self):
        class Sample(BaseModel):
            name: str

        schema = introspect_class(Sample)

        # Pydantic runs first, so it takes precedence
        assert schema.fields["name"].source == FieldSource.PYDANTIC

    def test_property_takes_precedence_over_pydantic(self):
        class Sample(BaseModel):
            _name: str = "default"

            @property
            def name(self) -> str:
                return self._name

        schema = introspect_class(Sample)

        # Properties run before pydantic in the discovery order
        assert "name" in schema.fields
        assert schema.fields["name"].source == FieldSource.PROPERTY


class TestPydanticEdgeCases:
    def test_model_with_validators(self):
        from pydantic import field_validator

        class Sample(BaseModel):
            email: str

            @field_validator("email")
            @classmethod
            def validate_email(cls, v: str) -> str:
                if "@" not in v:
                    raise ValueError("Invalid email")
                return v

        schema = introspect_class(Sample)

        assert "email" in schema.fields
        assert schema.fields["email"].source == FieldSource.PYDANTIC

    def test_model_with_alias(self):
        class Sample(BaseModel):
            name: str = Field(alias="userName")

        schema = introspect_class(Sample)

        # The field should be discovered by its Python name, not alias
        assert "name" in schema.fields
        assert "userName" not in schema.fields

    def test_model_with_complex_types(self):
        class Inner(BaseModel):
            value: int

        class Outer(BaseModel):
            inner: Inner
            items: list[Inner]

        schema = introspect_class(Outer)

        assert "inner" in schema.fields
        assert "items" in schema.fields
        assert schema.fields["inner"].getter_signature.return_annotation == Inner
        assert schema.fields["items"].getter_signature.return_annotation == list[Inner]

    def test_class_with_model_fields_attr_not_detected_as_pydantic(self):
        class FakePydantic:
            model_fields = {"name": "not a FieldInfo"}
            model_config = {"frozen": False}
            name: str

        schema = introspect_class(FakePydantic)

        # Should be discovered as annotation, not pydantic
        assert "name" in schema.fields
        assert schema.fields["name"].source == FieldSource.ANNOTATION

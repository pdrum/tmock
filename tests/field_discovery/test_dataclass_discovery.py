from dataclasses import dataclass, field

from tmock.class_schema import FieldSource, introspect_class


class TestDataclassDiscovery:
    def test_discovers_dataclass_fields(self):
        @dataclass
        class Sample:
            name: str
            count: int

        schema = introspect_class(Sample)

        assert "name" in schema.fields
        assert "count" in schema.fields
        assert schema.fields["name"].source == FieldSource.DATACLASS
        assert schema.fields["count"].source == FieldSource.DATACLASS

    def test_getter_signature_has_correct_return_type(self):
        @dataclass
        class Sample:
            value: int

        schema = introspect_class(Sample)
        field_schema = schema.fields["value"]

        assert field_schema.getter_signature.return_annotation is int

    def test_mutable_dataclass_has_setters(self):
        @dataclass
        class Sample:
            name: str

        schema = introspect_class(Sample)
        field_schema = schema.fields["name"]

        assert field_schema.setter_signature is not None
        params = list(field_schema.setter_signature.parameters.values())
        assert len(params) == 1
        assert params[0].name == "value"
        assert params[0].annotation is str

    def test_frozen_dataclass_has_no_setters(self):
        @dataclass(frozen=True)
        class Sample:
            name: str
            count: int

        schema = introspect_class(Sample)

        assert schema.fields["name"].setter_signature is None
        assert schema.fields["count"].setter_signature is None

    def test_field_with_default(self):
        @dataclass
        class Sample:
            name: str = "default"
            count: int = field(default=0)

        schema = introspect_class(Sample)

        assert "name" in schema.fields
        assert "count" in schema.fields

    def test_field_with_default_factory(self):
        @dataclass
        class Sample:
            items: list[str] = field(default_factory=list)

        schema = introspect_class(Sample)

        assert "items" in schema.fields
        field_schema = schema.fields["items"]
        assert field_schema.getter_signature.return_annotation == list[str]

    def test_skips_private_fields(self):
        @dataclass
        class Sample:
            public: str
            _private: str

        schema = introspect_class(Sample)

        assert "public" in schema.fields
        assert "_private" not in schema.fields

    def test_inherited_dataclass(self):
        @dataclass
        class Base:
            base_field: str

        @dataclass
        class Child(Base):
            child_field: int

        schema = introspect_class(Child)

        assert "base_field" in schema.fields
        assert "child_field" in schema.fields

    def test_dataclass_fields_not_in_methods(self):
        @dataclass
        class Sample:
            value: int

            def get_value(self) -> int:
                return self.value

        schema = introspect_class(Sample)

        assert "value" in schema.fields
        assert "value" not in schema.method_signatures
        assert "get_value" in schema.method_signatures

    def test_non_dataclass_returns_no_dataclass_fields(self):
        class NotADataclass:
            name: str

        schema = introspect_class(NotADataclass)

        # Should still discover via annotations, not dataclass
        assert "name" in schema.fields
        assert schema.fields["name"].source == FieldSource.ANNOTATION


class TestDataclassPrecedence:
    def test_dataclass_takes_precedence_over_annotation(self):
        @dataclass
        class Sample:
            name: str  # This is both a dataclass field and annotation

        schema = introspect_class(Sample)

        # Dataclass discovery runs before annotation discovery
        assert schema.fields["name"].source == FieldSource.DATACLASS

    def test_property_takes_precedence_over_dataclass(self):
        @dataclass
        class Sample:
            _name: str = "default"

            @property
            def name(self) -> str:
                return self._name

        schema = introspect_class(Sample)

        # Property discovery runs before dataclass discovery
        assert "name" in schema.fields
        assert schema.fields["name"].source == FieldSource.PROPERTY

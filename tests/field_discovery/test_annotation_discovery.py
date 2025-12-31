from typing import ClassVar, Optional

from tmock.class_schema import FieldSource, introspect_class


class TestAnnotationDiscovery:
    def test_discovers_annotated_instance_variable(self):
        class Sample:
            name: str
            count: int

        schema = introspect_class(Sample)

        assert "name" in schema.fields
        assert "count" in schema.fields
        assert schema.fields["name"].source == FieldSource.ANNOTATION
        assert schema.fields["count"].source == FieldSource.ANNOTATION

    def test_getter_signature_has_correct_return_type(self):
        class Sample:
            value: int

        schema = introspect_class(Sample)
        field = schema.fields["value"]

        assert field.getter_signature.return_annotation is int

    def test_setter_signature_has_value_param(self):
        class Sample:
            name: str

        schema = introspect_class(Sample)
        field = schema.fields["name"]

        assert field.setter_signature is not None
        params = list(field.setter_signature.parameters.values())
        assert len(params) == 1
        assert params[0].name == "value"
        assert params[0].annotation is str

    def test_annotations_always_have_setters(self):
        class Sample:
            readonly_by_convention: str

        schema = introspect_class(Sample)
        field = schema.fields["readonly_by_convention"]

        # Annotations are always assumed to be settable
        assert field.setter_signature is not None

    def test_skips_classvar_annotations(self):
        class Sample:
            instance_var: str
            class_var: ClassVar[int] = 0

        schema = introspect_class(Sample)

        assert "instance_var" in schema.fields
        assert "class_var" not in schema.fields

    def test_skips_private_annotations(self):
        class Sample:
            _private: str
            __very_private: int

        schema = introspect_class(Sample)

        assert "_private" not in schema.fields
        assert "__very_private" not in schema.fields

    def test_optional_type_annotation(self):
        class Sample:
            maybe_name: Optional[str]

        schema = introspect_class(Sample)

        assert "maybe_name" in schema.fields
        field = schema.fields["maybe_name"]
        assert field.getter_signature.return_annotation == Optional[str]

    def test_complex_type_annotation(self):
        class Sample:
            items: list[dict[str, int]]

        schema = introspect_class(Sample)

        assert "items" in schema.fields
        field = schema.fields["items"]
        assert field.getter_signature.return_annotation == list[dict[str, int]]

    def test_inherited_annotations(self):
        class Base:
            base_field: str

        class Child(Base):
            child_field: int

        schema = introspect_class(Child)

        assert "base_field" in schema.fields
        assert "child_field" in schema.fields

    def test_annotation_with_default_value(self):
        class Sample:
            with_default: str = "default"

        schema = introspect_class(Sample)

        assert "with_default" in schema.fields
        assert schema.fields["with_default"].source == FieldSource.ANNOTATION

    def test_annotations_not_in_methods(self):
        class Sample:
            field: str

            def method(self) -> str:
                return self.field

        schema = introspect_class(Sample)

        assert "field" in schema.fields
        assert "field" not in schema.method_signatures
        assert "method" in schema.method_signatures


class TestAnnotationPrecedence:
    def test_property_takes_precedence_over_annotation(self):
        class Sample:
            name: str  # annotation

            @property
            def name(self) -> str:  # property should win
                return "prop"

        schema = introspect_class(Sample)

        assert "name" in schema.fields
        # Property takes precedence over annotation
        assert schema.fields["name"].source == FieldSource.PROPERTY

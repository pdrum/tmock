from inspect import Signature

from tmock.class_schema import FieldSource, introspect_class


class TestPropertyDiscovery:
    def test_discovers_readonly_property(self):
        class Sample:
            @property
            def name(self) -> str:
                return "test"

        schema = introspect_class(Sample)

        assert "name" in schema.fields
        field = schema.fields["name"]
        assert field.source == FieldSource.PROPERTY
        assert field.setter_signature is None

    def test_discovers_readwrite_property(self):
        class Sample:
            _value: int = 0

            @property
            def value(self) -> int:
                return self._value

            @value.setter
            def value(self, value: int) -> None:
                self._value = value

        schema = introspect_class(Sample)

        assert "value" in schema.fields
        field = schema.fields["value"]
        assert field.source == FieldSource.PROPERTY
        assert field.setter_signature is not None

    def test_getter_signature_has_return_type(self):
        class Sample:
            @property
            def count(self) -> int:
                return 42

        schema = introspect_class(Sample)
        field = schema.fields["count"]

        assert field.getter_signature.return_annotation is int

    def test_setter_signature_has_value_param(self):
        class Sample:
            _name: str = ""

            @property
            def name(self) -> str:
                return self._name

            @name.setter
            def name(self, value: str) -> None:
                self._name = value

        schema = introspect_class(Sample)
        field = schema.fields["name"]

        assert field.setter_signature is not None
        params = list(field.setter_signature.parameters.values())
        assert len(params) == 1
        assert params[0].name == "value"
        assert params[0].annotation is str

    def test_property_defined_as_class_method_not_included(self):
        class Sample:
            @classmethod
            @property
            def invalid_prop(cls) -> str:
                return "invalid"

        schema = introspect_class(Sample)

        assert "invalid_prop" not in schema.fields

    def test_property_without_type_hints(self):
        class Sample:
            @property
            def untyped(self):
                return "value"

        schema = introspect_class(Sample)

        assert "untyped" in schema.fields
        field = schema.fields["untyped"]
        assert field.getter_signature.return_annotation is Signature.empty

    def test_skips_private_properties(self):
        class Sample:
            @property
            def _private(self) -> str:
                return "secret"

        schema = introspect_class(Sample)

        assert "_private" not in schema.fields

    def test_inherited_property(self):
        class Base:
            @property
            def base_prop(self) -> int:
                return 1

        class Child(Base):
            pass

        schema = introspect_class(Child)

        assert "base_prop" in schema.fields
        assert schema.fields["base_prop"].source == FieldSource.PROPERTY

    def test_overridden_property(self):
        class Base:
            @property
            def value(self) -> int:
                return 1

        class Child(Base):
            @property
            def value(self) -> int:
                return 2

        schema = introspect_class(Child)

        assert "value" in schema.fields
        assert schema.fields["value"].source == FieldSource.PROPERTY

    def test_property_not_in_methods(self):
        class Sample:
            @property
            def prop(self) -> str:
                return "value"

            def method(self) -> str:
                return "method"

        schema = introspect_class(Sample)

        assert "prop" in schema.fields
        assert "prop" not in schema.method_signatures
        assert "method" in schema.method_signatures
        assert "method" not in schema.fields

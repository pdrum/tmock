"""Edge cases for forward reference handling."""

from tmock import given, tpatch


class TestUnresolvableForwardRef:
    def test_falls_back_gracefully(self) -> None:
        """If a forward ref can't be resolved, validation should be skipped."""
        with tpatch.function("tests.forward_refs.fixtures.unresolvable_ref") as mock:
            given().call(mock()).returns("anything")

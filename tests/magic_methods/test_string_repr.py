import pytest

from tmock import given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError


class User:
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return f"User({self.name})"

    def __repr__(self) -> str:
        return f"<User name={self.name}>"

    def __format__(self, format_spec: str) -> str:
        return self.name


class SimpleObject:
    """Uses default object __str__ and __repr__."""

    pass


class TestStringRepresentation:
    def test_str_stubbing(self):
        mock = tmock(User)
        given().call(mock.__str__()).returns("MockedUser")

        assert str(mock) == "MockedUser"
        verify().call(mock.__str__()).once()

    def test_repr_stubbing(self):
        mock = tmock(User)
        given().call(mock.__repr__()).returns("<MockedRepr>")

        assert repr(mock) == "<MockedRepr>"
        verify().call(mock.__repr__()).once()

    def test_format_stubbing(self):
        mock = tmock(User)
        given().call(mock.__format__("")).returns("FormattedUser")

        # f-strings use __format__
        assert f"{mock}" == "FormattedUser"
        verify().call(mock.__format__("")).once()

    def test_strictness_str_raises(self):
        """If __str__ is defined, it must be stubbed."""
        mock = tmock(User)
        with pytest.raises(TMockUnexpectedCallError):
            str(mock)

    def test_strictness_repr_raises(self):
        """If __repr__ is defined, it must be stubbed."""
        mock = tmock(User)
        with pytest.raises(TMockUnexpectedCallError):
            repr(mock)

    def test_return_type_validation(self):
        mock = tmock(User)
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock.__str__()).returns(123)
        assert "Invalid return type" in str(exc.value)

    def test_fallback_str(self):
        """If not defined, str(mock) should use TMock's default repr."""
        mock = tmock(SimpleObject)

        # Should not crash
        s = str(mock)
        assert "<TMock of SimpleObject>" in s

        # Verify no interception
        assert not _is_intercepted(mock, "__str__")

    def test_fallback_repr(self):
        """If not defined, repr(mock) should use TMock's default repr."""
        mock = tmock(SimpleObject)

        r = repr(mock)
        assert "<TMock of SimpleObject>" in r

        assert not _is_intercepted(mock, "__repr__")


def _is_intercepted(mock, method_name):
    interceptors = object.__getattribute__(mock, "__method_interceptors")
    return method_name in interceptors

import pytest

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockUnexpectedCallError, TMockVerificationError


class Person:
    name: str
    age: int


class TestUnstubbed:
    def test_unstubbed_setter_error_message(self):
        mock = tmock(Person)

        with pytest.raises(TMockUnexpectedCallError) as exc_info:
            mock.name = "Alice"

        assert str(exc_info.value) == "No matching behavior defined on Person for set name = 'Alice'"

    def test_wrong_value_error_message(self):
        mock = tmock(Person)
        given().set(mock.name, "Alice").returns(None)

        with pytest.raises(TMockUnexpectedCallError) as exc_info:
            mock.name = "Bob"

        assert str(exc_info.value) == "No matching behavior defined on Person for set name = 'Bob'"


class TestVerificationTimes:
    def test_once_failure(self):
        mock = tmock(Person)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"
        mock.name = "Alice"

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().set(mock.name, "Alice").once()

        assert str(exc_info.value) == ("Expected set name = 'Alice' to be called 1 time(s), but was called 2 time(s)")

    def test_times_failure(self):
        mock = tmock(Person)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().set(mock.name, any(str)).times(3)

        assert str(exc_info.value) == "Expected set name = any(str) to be called 3 time(s), but was called 1 time(s)"

    def test_never_failure(self):
        mock = tmock(Person)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().set(mock.name, any(str)).never()

        assert str(exc_info.value) == ("Expected set name = any(str) to be called 0 time(s), but was called 1 time(s)")

    def test_at_least_failure(self):
        mock = tmock(Person)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().set(mock.name, any(str)).at_least(3)

        assert str(exc_info.value) == (
            "Expected set name = any(str) to be called at least 3 time(s), but was called 1 time(s)"
        )

    def test_at_most_failure(self):
        mock = tmock(Person)
        given().set(mock.name, any(str)).returns(None)

        mock.name = "Alice"
        mock.name = "Bob"
        mock.name = "Charlie"

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().set(mock.name, any(str)).at_most(2)

        assert str(exc_info.value) == (
            "Expected set name = any(str) to be called at most 2 time(s), but was called 3 time(s)"
        )

import pytest

from tmock import given, tmock, verify
from tmock.exceptions import TMockUnexpectedCallError, TMockVerificationError


class Person:
    name: str
    age: int


class TestUnstubbed:
    def test_unstubbed_getter_error_message(self):
        mock = tmock(Person)

        with pytest.raises(TMockUnexpectedCallError) as exc_info:
            _ = mock.name

        assert str(exc_info.value) == "No matching behavior defined on Person for get name"


class TestVerificationTimes:
    def test_once_failure(self):
        mock = tmock(Person)
        given().get(mock.name).returns("Alice")

        _ = mock.name
        _ = mock.name

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().get(mock.name).once()

        assert str(exc_info.value) == "Expected get name to be called 1 time(s), but was called 2 time(s)"

    def test_times_failure(self):
        mock = tmock(Person)
        given().get(mock.name).returns("Alice")

        _ = mock.name

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().get(mock.name).times(3)

        assert str(exc_info.value) == "Expected get name to be called 3 time(s), but was called 1 time(s)"

    def test_never_failure(self):
        mock = tmock(Person)
        given().get(mock.name).returns("Alice")

        _ = mock.name

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().get(mock.name).never()

        assert str(exc_info.value) == "Expected get name to be called 0 time(s), but was called 1 time(s)"

    def test_at_least_failure(self):
        mock = tmock(Person)
        given().get(mock.name).returns("Alice")

        _ = mock.name

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().get(mock.name).at_least(3)

        assert str(exc_info.value) == "Expected get name to be called at least 3 time(s), but was called 1 time(s)"

    def test_at_most_failure(self):
        mock = tmock(Person)
        given().get(mock.name).returns("Alice")

        _ = mock.name
        _ = mock.name
        _ = mock.name

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().get(mock.name).at_most(2)

        assert str(exc_info.value) == "Expected get name to be called at most 2 time(s), but was called 3 time(s)"

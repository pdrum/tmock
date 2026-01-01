import pytest

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockUnexpectedCallError, TMockVerificationError


class Calculator:
    def add(self, a: int, b: int) -> int:
        return 0

    def greet(self, name: str) -> str:
        return ""


class TestUnstubbed:
    def test_unstubbed_method_error_message(self):
        mock = tmock(Calculator)

        with pytest.raises(TMockUnexpectedCallError) as exc_info:
            mock.add(1, 2)

        assert str(exc_info.value) == "No matching behavior defined on Calculator for add(a=1, b=2)"

    def test_wrong_args_error_message(self):
        mock = tmock(Calculator)
        given().call(mock.add(1, 2)).returns(3)

        with pytest.raises(TMockUnexpectedCallError) as exc_info:
            mock.add(3, 4)

        assert str(exc_info.value) == "No matching behavior defined on Calculator for add(a=3, b=4)"

    def test_string_arg_error_message(self):
        mock = tmock(Calculator)

        with pytest.raises(TMockUnexpectedCallError) as exc_info:
            mock.greet("Alice")

        assert str(exc_info.value) == "No matching behavior defined on Calculator for greet(name='Alice')"


class TestVerificationTimes:
    def test_once_failure(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)

        mock.add(1, 2)
        mock.add(1, 2)

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.add(1, 2)).once()

        assert str(exc_info.value) == "Expected add(a=1, b=2) to be called 1 time(s), but was called 2 time(s)"

    def test_times_failure(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)

        mock.add(1, 2)

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.add(any(int), any(int))).times(3)

        assert str(exc_info.value) == (
            "Expected add(a=any(int), b=any(int)) to be called 3 time(s), but was called 1 time(s)"
        )

    def test_never_failure(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)

        mock.add(1, 2)

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.add(any(int), any(int))).never()

        assert str(exc_info.value) == (
            "Expected add(a=any(int), b=any(int)) to be called 0 time(s), but was called 1 time(s)"
        )

    def test_at_least_failure(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)

        mock.add(1, 2)

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.add(any(int), any(int))).at_least(3)

        assert str(exc_info.value) == (
            "Expected add(a=any(int), b=any(int)) to be called at least 3 time(s), but was called 1 time(s)"
        )

    def test_at_most_failure(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)

        mock.add(1, 2)
        mock.add(3, 4)
        mock.add(5, 6)

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.add(any(int), any(int))).at_most(2)

        assert str(exc_info.value) == (
            "Expected add(a=any(int), b=any(int)) to be called at most 2 time(s), but was called 3 time(s)"
        )

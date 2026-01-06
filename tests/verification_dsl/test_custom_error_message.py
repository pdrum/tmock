import pytest

from tmock import given, tmock, verify
from tmock.exceptions import TMockVerificationError


class Service:
    def action(self, arg: int) -> None:
        pass


class TestCustomErrorMessage:
    def test_custom_error_message_once(self):
        mock = tmock(Service)
        given().call(mock.action(1)).returns(None)

        with pytest.raises(TMockVerificationError) as exc:
            verify().call(mock.action(1)).once(error_message="Should have called action(1)")

        expected = (
            "Should have called action(1)\nOriginal error: Expected action(arg=1) to be called 1 time(s), "
            "but was called 0 time(s)"
        )
        assert str(exc.value) == expected

    def test_custom_error_message_times(self):
        mock = tmock(Service)
        given().call(mock.action(1)).returns(None)

        mock.action(1)

        with pytest.raises(TMockVerificationError) as exc:
            verify().call(mock.action(1)).times(2, error_message="Expected 2 calls")

        expected = (
            "Expected 2 calls\nOriginal error: Expected action(arg=1) to be called 2 time(s), but was called 1 time(s)"
        )
        assert str(exc.value) == expected

    def test_custom_error_message_never(self):
        mock = tmock(Service)
        given().call(mock.action(1)).returns(None)

        mock.action(1)

        with pytest.raises(TMockVerificationError) as exc:
            verify().call(mock.action(1)).never(error_message="Should NOT have called action(1)")

        expected = (
            "Should NOT have called action(1)\nOriginal error: Expected action(arg=1) to be called 0 time(s), "
            "but was called 1 time(s)"
        )
        assert str(exc.value) == expected

    def test_custom_error_message_at_least(self):
        mock = tmock(Service)
        given().call(mock.action(1)).returns(None)

        with pytest.raises(TMockVerificationError) as exc:
            verify().call(mock.action(1)).at_least(1, error_message="At least one call required")

        expected = (
            "At least one call required\nOriginal error: Expected action(arg=1) to be called "
            "at least 1 time(s), but was called 0 time(s)"
        )
        assert str(exc.value) == expected

    def test_custom_error_message_at_most(self):
        mock = tmock(Service)
        given().call(mock.action(1)).returns(None)

        mock.action(1)
        mock.action(1)

        with pytest.raises(TMockVerificationError) as exc:
            verify().call(mock.action(1)).at_most(1, error_message="Too many calls")

        expected = (
            "Too many calls\nOriginal error: Expected action(arg=1) to be called at most 1 time(s), "
            "but was called 2 time(s)"
        )
        assert str(exc.value) == expected

import pytest

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockVerificationError


class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b

    def greet(self, name: str, greeting: str = "Hello") -> str:
        return f"{greeting}, {name}!"

    def no_args(self) -> int:
        return 42


class TestVerifyCalled:
    def test_called_passes_when_method_was_called(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        verify().call(mock.add(1, 2)).called()

    def test_called_fails_when_method_was_not_called(self):
        mock = tmock(Calculator)
        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.add(1, 2)).called()
        assert "to be called at least 1 time(s), but was called 0 time(s)" in str(exc_info.value)

    def test_called_fails_when_called_with_different_args(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        with pytest.raises(TMockVerificationError):
            verify().call(mock.add(3, 4)).called()


class TestVerifyOnce:
    def test_once_passes_when_called_exactly_once(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        verify().call(mock.add(1, 2)).once()

    def test_once_fails_when_never_called(self):
        mock = tmock(Calculator)
        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.add(1, 2)).once()
        assert "to be called 1 time(s), but was called 0 time(s)" in str(exc_info.value)

    def test_once_fails_when_called_multiple_times(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        mock.add(1, 2)
        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.add(1, 2)).once()
        assert "to be called 1 time(s), but was called 2 time(s)" in str(exc_info.value)


class TestVerifyTimes:
    def test_times_passes_with_exact_count(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        mock.add(1, 2)
        mock.add(1, 2)
        verify().call(mock.add(1, 2)).times(3)

    def test_times_fails_when_count_is_less(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        with pytest.raises(TMockVerificationError):
            verify().call(mock.add(1, 2)).times(3)

    def test_times_fails_when_count_is_more(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        mock.add(1, 2)
        mock.add(1, 2)
        with pytest.raises(TMockVerificationError):
            verify().call(mock.add(1, 2)).times(2)

    def test_times_zero_same_as_never(self):
        mock = tmock(Calculator)
        verify().call(mock.add(1, 2)).times(0)


class TestVerifyNever:
    def test_never_passes_when_not_called(self):
        mock = tmock(Calculator)
        verify().call(mock.add(1, 2)).never()

    def test_never_fails_when_called_once(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.add(1, 2)).never()
        assert "to be called 0 time(s), but was called 1 time(s)" in str(exc_info.value)

    def test_never_passes_when_called_with_different_args(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        verify().call(mock.add(3, 4)).never()


class TestVerifyAtLeast:
    def test_at_least_passes_when_count_equals_minimum(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        mock.add(1, 2)
        verify().call(mock.add(1, 2)).at_least(2)

    def test_at_least_passes_when_count_exceeds_minimum(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        mock.add(1, 2)
        mock.add(1, 2)
        verify().call(mock.add(1, 2)).at_least(2)

    def test_at_least_fails_when_count_below_minimum(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        with pytest.raises(TMockVerificationError):
            verify().call(mock.add(1, 2)).at_least(2)


class TestVerifyAtMost:
    def test_at_most_passes_when_count_equals_maximum(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        mock.add(1, 2)
        verify().call(mock.add(1, 2)).at_most(2)

    def test_at_most_passes_when_count_below_maximum(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        verify().call(mock.add(1, 2)).at_most(2)

    def test_at_most_fails_when_count_exceeds_maximum(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        mock.add(1, 2)
        mock.add(1, 2)
        with pytest.raises(TMockVerificationError):
            verify().call(mock.add(1, 2)).at_most(2)

    def test_at_most_zero_same_as_never(self):
        mock = tmock(Calculator)
        verify().call(mock.add(1, 2)).at_most(0)


class TestVerifyWithKwargs:
    def test_verify_with_kwargs(self):
        mock = tmock(Calculator)
        given().call(mock.greet(any(str), greeting=any(str))).returns("")
        mock.greet("Alice", greeting="Hi")
        verify().call(mock.greet("Alice", greeting="Hi")).once()

    def test_verify_kwargs_must_match(self):
        mock = tmock(Calculator)
        given().call(mock.greet(any(str), greeting=any(str))).returns("")
        mock.greet("Alice", greeting="Hi")
        with pytest.raises(TMockVerificationError):
            verify().call(mock.greet("Alice", greeting="Hello")).called()

    def test_verify_with_default_kwargs(self):
        mock = tmock(Calculator)
        given().call(mock.greet(any(str), greeting=any(str))).returns("")
        mock.greet("Alice")
        verify().call(mock.greet("Alice")).once()


class TestVerifyWithNoArgs:
    def test_verify_no_arg_method(self):
        mock = tmock(Calculator)
        given().call(mock.no_args()).returns(0)
        mock.no_args()
        verify().call(mock.no_args()).once()


class TestVerifyWithStubbing:
    def test_verify_works_after_stubbing(self):
        mock = tmock(Calculator)
        given().call(mock.add(1, 2)).returns(100)

        result = mock.add(1, 2)
        assert result == 100

        verify().call(mock.add(1, 2)).once()

    def test_stubbing_calls_not_counted_in_verification(self):
        mock = tmock(Calculator)
        given().call(mock.add(1, 2)).returns(100)
        # Stubbing should not count as a call
        # Only actual usage counts
        mock.add(1, 2)
        verify().call(mock.add(1, 2)).once()

    def test_multiple_verifications_on_same_mock(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        mock.add(3, 4)

        verify().call(mock.add(1, 2)).once()
        verify().call(mock.add(3, 4)).once()


class TestVerifyErrorMessages:
    def test_error_message_includes_method_name_and_args(self):
        mock = tmock(Calculator)
        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.add(1, 2)).called()
        assert "add(a=1, b=2)" in str(exc_info.value)

    def test_error_message_includes_kwargs(self):
        mock = tmock(Calculator)
        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.greet("Alice", greeting="Hi")).called()
        error_msg = str(exc_info.value)
        assert "greet(" in error_msg
        assert "name='Alice'" in error_msg
        assert "greeting='Hi'" in error_msg


class TestArgumentNormalization:
    """Tests that positional and keyword arguments are treated equivalently."""

    def test_positional_call_verified_with_kwargs(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)  # positional
        verify().call(mock.add(a=1, b=2)).once()  # kwargs

    def test_kwargs_call_verified_with_positional(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(a=1, b=2)  # kwargs
        verify().call(mock.add(1, 2)).once()  # positional

    def test_mixed_args_are_equivalent(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, b=2)  # mixed
        verify().call(mock.add(a=1, b=2)).once()  # all kwargs
        # Call again for second verification
        mock.add(1, b=2)
        verify().call(mock.add(1, 2)).times(2)  # all positional

    def test_stubbing_with_kwargs_matches_positional_call(self):
        mock = tmock(Calculator)
        given().call(mock.add(a=1, b=2)).returns(100)
        result = mock.add(1, 2)  # positional
        assert result == 100

    def test_stubbing_with_positional_matches_kwargs_call(self):
        mock = tmock(Calculator)
        given().call(mock.add(1, 2)).returns(100)
        result = mock.add(a=1, b=2)  # kwargs
        assert result == 100


class TestVerifyEdgeCases:
    def test_verification_error_is_assertion_error(self):
        mock = tmock(Calculator)
        with pytest.raises(AssertionError):
            verify().call(mock.add(1, 2)).called()

    def test_verify_without_mock_call_raises_error(self):
        with pytest.raises(TMockStubbingError) as exc_info:
            verify().call(None).called()
        assert "verify() was called but no mock method was invoked" in str(exc_info.value)

    def test_verify_distinguishes_calls_by_args(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        mock.add(1, 2)
        mock.add(3, 4)

        verify().call(mock.add(1, 2)).times(2)
        verify().call(mock.add(3, 4)).once()

    def test_verify_same_method_different_args_independently(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 1)
        mock.add(2, 2)
        mock.add(3, 3)

        verify().call(mock.add(1, 1)).once()
        verify().call(mock.add(2, 2)).once()
        verify().call(mock.add(3, 3)).once()
        verify().call(mock.add(4, 4)).never()


class TestIncompleteVerificationDetection:
    """Tests that incomplete verify().call() calls are detected and raise errors."""

    def test_incomplete_verify_detected_on_next_mock_call(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        verify().call(mock.add(1, 2))  # Forgot .once(), .called(), etc.

        with pytest.raises(TMockVerificationError) as exc_info:
            mock.add(3, 4)  # Next mock call should detect incomplete verification

        assert "Incomplete verification" in str(exc_info.value)
        assert "verify().call(add(a=1, b=2))" in str(exc_info.value)
        assert ".once()" in str(exc_info.value) or ".called()" in str(exc_info.value)

    def test_incomplete_verify_detected_on_next_verify(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        verify().call(mock.add(1, 2))  # Forgot .once()

        with pytest.raises(TMockVerificationError) as exc_info:
            verify().call(mock.add(1, 2))  # Next verify() should detect incomplete

        assert "Incomplete verification" in str(exc_info.value)

    def test_incomplete_verify_detected_on_given(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        verify().call(mock.add(1, 2))  # Forgot .once()

        with pytest.raises(TMockVerificationError) as exc_info:
            given().call(mock.add(1, 2))  # given() should detect incomplete verify

        assert "Incomplete verification" in str(exc_info.value)

    def test_complete_verification_allows_subsequent_operations(self):
        mock = tmock(Calculator)
        given().call(mock.add(any(int), any(int))).returns(0)
        mock.add(1, 2)
        verify().call(mock.add(1, 2)).once()  # Complete verification

        # Should not raise - verification was completed
        mock.add(3, 4)
        verify().call(mock.add(3, 4)).once()

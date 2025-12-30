import pytest

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockUnexpectedCallError


class TestAnyMatcherStubbing:
    def test_any_matcher_matches_any_value_of_type(self):
        class SampleClass:
            def foo(self, x: int) -> str:
                return ""

        mock = tmock(SampleClass)
        given().call(mock.foo(any(int))).returns("matched")

        assert mock.foo(1) == "matched"
        assert mock.foo(999) == "matched"
        assert mock.foo(-42) == "matched"

    def test_any_matcher_does_not_match_wrong_type(self):
        class SampleClass:
            def foo(self, x: int) -> str:
                return ""

        mock = tmock(SampleClass)
        given().call(mock.foo(any(str))).returns("matched")

        with pytest.raises(TMockUnexpectedCallError):
            mock.foo(42)

    def test_any_matcher_with_multiple_args(self):
        class SampleClass:
            def foo(self, x: int, y: str) -> str:
                return ""

        mock = tmock(SampleClass)
        given().call(mock.foo(any(int), "hello")).returns("matched")

        assert mock.foo(1, "hello") == "matched"
        assert mock.foo(999, "hello") == "matched"
        with pytest.raises(TMockUnexpectedCallError):
            mock.foo(1, "world")


class TestAnyMatcherVerification:
    def test_any_matcher_verifies_calls_with_any_value(self):
        class SampleClass:
            def foo(self, x: int) -> None:
                pass

        mock = tmock(SampleClass)
        given().call(mock.foo(any(int))).returns(None)
        mock.foo(1)
        mock.foo(2)
        mock.foo(3)

        verify().call(mock.foo(any(int))).times(3)

    def test_any_matcher_verification_with_mixed_args(self):
        class SampleClass:
            def foo(self, x: int, y: str) -> None:
                pass

        mock = tmock(SampleClass)
        given().call(mock.foo(any(int), any(str))).returns(None)
        mock.foo(1, "hello")
        mock.foo(2, "hello")
        mock.foo(3, "world")

        verify().call(mock.foo(any(int), "hello")).times(2)
        verify().call(mock.foo(any(int), "world")).once()

    def test_any_matcher_type_mismatch_in_verification(self):
        class SampleClass:
            def foo(self, x: int) -> None:
                pass

        mock = tmock(SampleClass)
        given().call(mock.foo(any(int))).returns(None)
        mock.foo(42)

        verify().call(mock.foo(any(str))).never()
        verify().call(mock.foo(any(int))).once()


class TestMatcherMisuse:
    """Tests that matchers in actual calls don't accidentally match patterns."""

    def test_any_in_actual_call_does_not_match_any_in_stub(self):
        class SampleClass:
            def foo(self, x: int) -> str:
                return ""

        mock = tmock(SampleClass)
        given().call(mock.foo(any(int))).returns("matched")

        # Misuse: matcher in actual call should not match any in stub
        with pytest.raises(TMockUnexpectedCallError):
            mock.foo(any(int))

    def test_matcher_in_actual_call_raises_with_stub_present(self):
        class SampleClass:
            def foo(self, x: int) -> None:
                pass

        mock = tmock(SampleClass)
        given().call(mock.foo(any(int))).returns(None)

        # Misuse: matcher in actual call doesn't match the any(int) pattern
        # because the matcher object itself is not an int
        with pytest.raises(TMockUnexpectedCallError):
            mock.foo(any(int))

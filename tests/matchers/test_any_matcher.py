from tmock import any, given, tmock, verify


class TestAnyMatcherStubbing:
    def test_any_matcher_matches_any_value_of_type(self):
        class SampleClass:
            def foo(self, x: int) -> str:
                return ""

        mock = tmock(SampleClass)
        given(mock.foo(any(int))).returns("matched")

        assert mock.foo(1) == "matched"
        assert mock.foo(999) == "matched"
        assert mock.foo(-42) == "matched"

    def test_any_matcher_does_not_match_wrong_type(self):
        class SampleClass:
            def foo(self, x: int) -> str:
                return ""

        mock = tmock(SampleClass)
        given(mock.foo(any(str))).returns("matched")

        assert mock.foo(42) is None

    def test_any_matcher_with_multiple_args(self):
        class SampleClass:
            def foo(self, x: int, y: str) -> str:
                return ""

        mock = tmock(SampleClass)
        given(mock.foo(any(int), "hello")).returns("matched")

        assert mock.foo(1, "hello") == "matched"
        assert mock.foo(999, "hello") == "matched"
        assert mock.foo(1, "world") is None


class TestAnyMatcherVerification:
    def test_any_matcher_verifies_calls_with_any_value(self):
        class SampleClass:
            def foo(self, x: int) -> None:
                pass

        mock = tmock(SampleClass)
        mock.foo(1)
        mock.foo(2)
        mock.foo(3)

        verify(mock.foo(any(int))).times(3)

    def test_any_matcher_verification_with_mixed_args(self):
        class SampleClass:
            def foo(self, x: int, y: str) -> None:
                pass

        mock = tmock(SampleClass)
        mock.foo(1, "hello")
        mock.foo(2, "hello")
        mock.foo(3, "world")

        verify(mock.foo(any(int), "hello")).times(2)
        verify(mock.foo(any(int), "world")).once()

    def test_any_matcher_type_mismatch_in_verification(self):
        class SampleClass:
            def foo(self, x: int) -> None:
                pass

        mock = tmock(SampleClass)
        mock.foo(42)

        verify(mock.foo(any(str))).never()
        verify(mock.foo(any(int))).once()

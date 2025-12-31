import pytest

from tmock import given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError


class TestStubbingDsl:
    def test_stubbing_call_with_no_arg_with_return_value(self):
        class SampleClass:
            def foo(self) -> int:
                return 100

        mock = tmock(SampleClass)
        given().call(mock.foo()).returns(20)
        assert mock.foo() == 20

    def test_stubbing_call_with_arg_with_return_value(self):
        class SampleClass:
            def foo(self, arg: int) -> int:
                return 100

        mock = tmock(SampleClass)
        given().call(mock.foo(10)).returns(20)
        assert mock.foo(10) == 20
        with pytest.raises(TMockUnexpectedCallError):
            mock.foo(15)

    def test_stubbing_multiple_calls_with_different_args(self):
        class SampleClass:
            def foo(self, x: int) -> str:
                return ""

        mock = tmock(SampleClass)
        given().call(mock.foo(1)).returns("one")
        given().call(mock.foo(2)).returns("two")
        assert mock.foo(1) == "one"
        assert mock.foo(2) == "two"
        with pytest.raises(TMockUnexpectedCallError):
            mock.foo(3)

    def test_later_stub_overrides_earlier_for_same_args(self):
        class SampleClass:
            def foo(self, x: int) -> str:
                return ""

        mock = tmock(SampleClass)
        given().call(mock.foo(1)).returns("first")
        given().call(mock.foo(1)).returns("second")

        assert mock.foo(1) == "second"

    def test_later_stub_overrides_earlier_with_matchers(self):
        from tmock import any

        class SampleClass:
            def foo(self, x: int) -> str:
                return ""

        mock = tmock(SampleClass)
        given().call(mock.foo(any(int))).returns("any")
        given().call(mock.foo(1)).returns("specific")

        # Specific stub added later wins for value 1
        assert mock.foo(1) == "specific"
        # Other values still match the any() stub
        assert mock.foo(2) == "any"

    def test_more_specific_stub_added_earlier_loses_to_general_stub(self):
        from tmock import any

        class SampleClass:
            def foo(self, x: int) -> str:
                return ""

        mock = tmock(SampleClass)
        given().call(mock.foo(1)).returns("specific")
        given().call(mock.foo(any(int))).returns("any")

        # Later any() stub wins even for value 1
        assert mock.foo(1) == "any"
        assert mock.foo(2) == "any"


class TestIncompleteStubDetection:
    """Tests that incomplete given().call() calls are detected and raise errors."""

    def test_incomplete_stub_detected_on_next_mock_call(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return 0

        mock = tmock(SampleClass)
        given().call(mock.foo(1))  # Forgot .returns()

        with pytest.raises(TMockStubbingError) as exc_info:
            mock.foo(2)  # Next mock call should detect incomplete stub

        assert "Incomplete stub" in str(exc_info.value)
        assert "call(foo(x=1))" in str(exc_info.value)
        assert ".returns()" in str(exc_info.value)

    def test_incomplete_stub_detected_on_next_given(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return 0

        mock = tmock(SampleClass)
        given().call(mock.foo(1))  # Forgot .returns()

        with pytest.raises(TMockStubbingError) as exc_info:
            given().call(mock.foo(2))  # Next given() should detect incomplete stub

        assert "Incomplete stub" in str(exc_info.value)
        assert "foo(x=1)" in str(exc_info.value)

    def test_incomplete_stub_detected_on_verify(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return 0

        mock = tmock(SampleClass)
        given().call(mock.foo(1))  # Forgot .returns()

        with pytest.raises(TMockStubbingError) as exc_info:
            verify().call(mock.foo(1))  # verify() should detect incomplete stub

        assert "Incomplete stub" in str(exc_info.value)

    def test_complete_stub_allows_subsequent_operations(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return 0

        mock = tmock(SampleClass)
        given().call(mock.foo(1)).returns(100)  # Complete stub

        # Should not raise - stub was completed
        assert mock.foo(1) == 100
        given().call(mock.foo(2)).returns(200)
        assert mock.foo(2) == 200

import pytest

from tmock import checks, define, tmock
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError


class TestStubbingDsl:
    def test_stubbing_call_with_no_arg_with_return_value(self):
        class SampleClass:
            def foo(self) -> int:
                return 100

        mock = tmock(SampleClass)
        define().given(mock.foo()).returns(20)
        assert mock.foo() == 20

    def test_stubbing_call_with_arg_with_return_value(self):
        class SampleClass:
            def foo(self, arg: int) -> int:
                return 100

        mock = tmock(SampleClass)
        define().given(mock.foo(10)).returns(20)
        assert mock.foo(10) == 20
        with pytest.raises(TMockUnexpectedCallError):
            mock.foo(15)

    def test_stubbing_multiple_calls_with_different_args(self):
        class SampleClass:
            def foo(self, x: int) -> str:
                return ""

        mock = tmock(SampleClass)
        define().given(mock.foo(1)).returns("one")
        define().given(mock.foo(2)).returns("two")
        assert mock.foo(1) == "one"
        assert mock.foo(2) == "two"
        with pytest.raises(TMockUnexpectedCallError):
            mock.foo(3)


class TestIncompleteStubDetection:
    """Tests that incomplete define().given() calls are detected and raise errors."""

    def test_incomplete_stub_detected_on_next_mock_call(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return 0

        mock = tmock(SampleClass)
        define().given(mock.foo(1))  # Forgot .returns()

        with pytest.raises(TMockStubbingError) as exc_info:
            mock.foo(2)  # Next mock call should detect incomplete stub

        assert "Incomplete stub" in str(exc_info.value)
        assert "given(foo(x=1))" in str(exc_info.value)
        assert ".returns()" in str(exc_info.value)

    def test_incomplete_stub_detected_on_next_define(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return 0

        mock = tmock(SampleClass)
        define().given(mock.foo(1))  # Forgot .returns()

        with pytest.raises(TMockStubbingError) as exc_info:
            define().given(mock.foo(2))  # Next define() should detect incomplete stub

        assert "Incomplete stub" in str(exc_info.value)
        assert "foo(x=1)" in str(exc_info.value)

    def test_incomplete_stub_detected_on_checks(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return 0

        mock = tmock(SampleClass)
        define().given(mock.foo(1))  # Forgot .returns()

        with pytest.raises(TMockStubbingError) as exc_info:
            checks().verify(mock.foo(1))  # checks() should detect incomplete stub

        assert "Incomplete stub" in str(exc_info.value)

    def test_complete_stub_allows_subsequent_operations(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return 0

        mock = tmock(SampleClass)
        define().given(mock.foo(1)).returns(100)  # Complete stub

        # Should not raise - stub was completed
        assert mock.foo(1) == 100
        define().given(mock.foo(2)).returns(200)
        assert mock.foo(2) == 200

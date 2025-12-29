from tmock import tmock
from tmock.stubbing_dsl import given


class TestStubbingDsl:
    def test_stubbing_call_with_no_arg_with_return_value(self):
        class SampleClass:
            def foo(self) -> int:
                return 100

        mock = tmock(SampleClass)
        given(mock.foo()).returns(20)
        assert mock.foo() == 20

    def test_stubbing_call_with_arg_with_return_value(self):
        class SampleClass:
            def foo(self, arg: int) -> int:
                return 100

        mock = tmock(SampleClass)
        given(mock.foo(10)).returns(20)
        assert mock.foo(10) == 20
        assert mock.foo(15) is None

    def test_stubbing_multiple_calls_with_different_args(self):
        class SampleClass:
            def foo(self, x: int) -> str:
                return ""

        mock = tmock(SampleClass)
        given(mock.foo(1)).returns("one")
        given(mock.foo(2)).returns("two")
        assert mock.foo(1) == "one"
        assert mock.foo(2) == "two"
        assert mock.foo(3) is None

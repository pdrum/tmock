from tmock import tmock
from tmock.stubbing_dsl import given


class TestStubbingDsl:
    def test_stubbing_call_with_no_arg_with_return_value(self):
        class SampleClass:
            def foo(self) -> int:
                return 100

        mocked_sample_class = tmock(SampleClass)
        given(mocked_sample_class.foo()).returns(20)
        assert mocked_sample_class.foo() == 20

    def test_stubbing_call_with_arg_with_return_value(self):
        class SampleClass:
            def foo(self, arg: int) -> int:
                return 100

        mocked_sample_class = tmock(SampleClass)
        given(mocked_sample_class.foo(10)).returns(20)
        assert mocked_sample_class.foo(10) == 20
        assert mocked_sample_class.foo(15) is None  # TODO: Should be an exception later

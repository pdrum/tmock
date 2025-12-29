from tmock import tmock
from tmock.stubbing_dsl import given


class TestMockEngine:

    def test_is_instance_check(self):
        class SampleClass:
            def __init__(self):
                raise ValueError('Expected the parent constructor not to be called')

        class OtherClass:
            pass

        assert isinstance(tmock(SampleClass), SampleClass)
        assert not isinstance(tmock(SampleClass), OtherClass)

    def test_recording_calls_with_no_arg(self, capsys):
        class SampleClass:
            def foo(self):
                print("foo")

        mocked_sample_class = tmock(SampleClass)
        mocked_sample_class.foo()
        assert len(mocked_sample_class.__tmock_state__.calls) == 1
        assert capsys.readouterr().out == ""

    def test_stubbing_call_with_no_arg_with_return_value(self):
        class SampleClass:
            def foo(self) -> int:
                return 100

        mocked_sample_class = tmock(SampleClass)
        given(mocked_sample_class.foo()).returns(20)
        assert mocked_sample_class.foo() == 20

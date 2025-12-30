import pytest

from tmock import given, tmock
from tmock.exceptions import TMockUnexpectedCallError


class TestMockEngine:
    def test_is_instance_check(self):
        class SampleClass:
            def __init__(self):
                raise ValueError("Expected the parent constructor not to be called")

        class OtherClass:
            pass

        assert isinstance(tmock(SampleClass), SampleClass)
        assert not isinstance(tmock(SampleClass), OtherClass)

    def test_not_executing_real_method(self, capsys):
        class SampleClass:
            def foo(self):
                print("foo")

        mocked_sample_class = tmock(SampleClass)
        given().call(mocked_sample_class.foo()).runs(lambda _: None)
        mocked_sample_class.foo()
        assert capsys.readouterr().out == ""

    def test_raising_exception_if_stub_not_defined(self, capsys):
        class SampleClass:
            def foo(self):
                print("foo")

        mocked_sample_class = tmock(SampleClass)
        with pytest.raises(TMockUnexpectedCallError):
            mocked_sample_class.foo()
        assert capsys.readouterr().out == ""

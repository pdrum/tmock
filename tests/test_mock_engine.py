from tmock import tmock


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
        mocked_sample_class.foo()
        assert capsys.readouterr().out == ""

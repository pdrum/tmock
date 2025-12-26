from tmock import tmock


class TestMockEngine:

    def test_is_instance_check_true(self):
        class SampleClass:
            def __init__(self):
                raise ValueError('Expected the parent constructor not to be called')

        class OtherClass:
            pass

        assert isinstance(tmock(SampleClass), SampleClass)
        assert not isinstance(tmock(SampleClass), OtherClass)

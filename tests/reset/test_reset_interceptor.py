import pytest

from tmock import given, reset, reset_behaviors, reset_interactions, tmock, tpatch, verify
from tmock.exceptions import TMockResetError, TMockUnexpectedCallError


def my_func(x: int) -> int:
    return x + 1


class TestResetInterceptor:
    def test_reset_function_mock(self):
        """Verify that reset() works on standalone function mocks."""
        mock = tmock(my_func)
        given().call(mock(1)).returns(10)

        assert mock(1) == 10
        verify().call(mock(1)).once()

        # Reset everything
        reset(mock)

        # Verify interaction is cleared
        verify().call(mock(1)).never()

        # Verify behavior is cleared (should raise error)
        with pytest.raises(TMockUnexpectedCallError):
            mock(1)

    def test_reset_patch(self):
        """Verify that reset() works on patched functions (which return interceptors)."""
        with tpatch.function("tests.reset.test_reset_interceptor.my_func") as mock:
            given().call(mock(1)).returns(99)

            assert my_func(1) == 99
            verify().call(mock(1)).once()

            # Reset
            reset(mock)

            verify().call(mock(1)).never()
            with pytest.raises(TMockUnexpectedCallError):
                my_func(1)

    def test_reset_invalid_object_raises_error(self):
        """Verify that reset() on a non-mock raises TMockResetError."""
        with pytest.raises(TMockResetError, match="not a valid tmock object"):
            reset("not a mock")

    def test_reset_interactions_only_on_interceptor(self):
        mock = tmock(my_func)
        given().call(mock(1)).returns(10)

        mock(1)
        verify().call(mock(1)).once()

        reset_interactions(mock)

        # Interaction cleared
        verify().call(mock(1)).never()
        # Behavior preserved
        assert mock(1) == 10

    def test_reset_behaviors_only_on_interceptor(self):
        mock = tmock(my_func)
        given().call(mock(1)).returns(10)

        mock(1)
        verify().call(mock(1)).once()

        reset_behaviors(mock)

        # Interaction preserved
        verify().call(mock(1)).once()
        # Behavior cleared
        with pytest.raises(TMockUnexpectedCallError):
            mock(1)

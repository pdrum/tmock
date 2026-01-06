from typing import Callable

import pytest

from tmock import given, tmock, verify
from tmock.exceptions import TMockStubbingError


def execute_callback(callback: Callable[[int], str], val: int) -> str:
    """A generic function that executes a provided callback."""
    return callback(val)


def module_function(x: int) -> str:
    return f"func-{x}"


class Service:
    def instance_method(self, x: int) -> str:
        return f"method-{x}"

    @classmethod
    def class_method(cls, x: int) -> str:
        return f"cls-{x}"

    @staticmethod
    def static_method(x: int) -> str:
        return f"static-{x}"


class TestMockFunctionIntegration:
    def test_mock_module_function_injection(self):
        """Scenario 1: Mocking a module function and passing it as a dependency."""
        # Create a standalone mock matching 'module_function' signature
        mock_func = tmock(module_function)

        given().call(mock_func(100)).returns("mocked-func")

        # Inject the mock into the system
        result = execute_callback(mock_func, 100)

        assert result == "mocked-func"
        verify().call(mock_func(100)).once()

    def test_mock_class_method_injection(self):
        """Scenario 2: Mocking an unbound class method and passing it."""
        # tmock(Service.class_method) creates a callable mock matching the signature
        # Note: Class methods passed as functions usually have 'cls' bound or not depending on access.
        # Accessing via Service.class_method gives a bound method (where cls is implicit).
        # inspect.signature on bound method drops first arg.
        # tmock handles this correctly.

        mock_cm = tmock(Service.class_method)

        given().call(mock_cm(200)).returns("mocked-cls")

        # Inject
        result = execute_callback(mock_cm, 200)

        assert result == "mocked-cls"
        verify().call(mock_cm(200)).once()

    def test_mock_static_method_injection(self):
        """Scenario 3: Mocking a static method and passing it."""
        mock_sm = tmock(Service.static_method)

        given().call(mock_sm(300)).returns("mocked-static")

        result = execute_callback(mock_sm, 300)

        assert result == "mocked-static"
        verify().call(mock_sm(300)).once()

    def test_mock_instance_method_injection(self):
        """Scenario 4: Mocking a bound instance method and passing it."""
        service = Service()
        # Mocking the bound method 'service.instance_method'
        # The signature of a bound method does not include 'self'.
        mock_im = tmock(service.instance_method)

        given().call(mock_im(400)).returns("mocked-method")

        result = execute_callback(mock_im, 400)

        assert result == "mocked-method"
        verify().call(mock_im(400)).once()

    def test_mock_unbound_instance_method_injection(self):
        """Additional Scenario: Mocking the UNBOUND instance method (Service.instance_method)."""
        # This expects explicit 'self' (or instance) as first argument.
        mock_unbound = tmock(Service.instance_method)

        # We need an instance to pass as first arg
        svc = Service()

        given().call(mock_unbound(svc, 500)).returns("mocked-unbound")

        # Execute manually since our helper 'execute_callback' only passes 1 arg
        with pytest.raises(TMockStubbingError) as exc_info:
            execute_callback(mock_unbound, 500)
        assert str(exc_info.value) == "Invalid args passed to instance_method => missing a required argument: 'x'"

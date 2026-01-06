from typing import Protocol, runtime_checkable

import pytest

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockUnexpectedCallError

# --- Protocols ---


@runtime_checkable
class Logger(Protocol):
    def log(self, message: str) -> None: ...


class DataStore(Protocol):
    def get_data(self, key: str) -> dict: ...

    @property
    def is_ready(self) -> bool: ...


# --- System Under Test ---


class App:
    def __init__(self, logger: Logger, store: DataStore):
        self.logger = logger
        self.store = store

    def run(self, key: str) -> str:
        if self.store.is_ready:
            data = self.store.get_data(key)
            self.logger.log(f"Processed {key}")
            return str(data.get("val", "empty"))
        return "not ready"


# --- Tests ---


class TestMockProtocol:
    def test_mock_protocol_methods(self):
        """Verify that methods defined in a Protocol are correctly intercepted."""
        mock_logger = tmock(Logger)

        # Stub log (returns None)
        given().call(mock_logger.log(any(str))).returns(None)

        mock_logger.log("test")

        verify().call(mock_logger.log("test")).once()

    def test_mock_protocol_properties(self):
        """Verify that properties in a Protocol are correctly intercepted."""
        mock_store = tmock(DataStore)

        # Stub property getter
        given().get(mock_store.is_ready).returns(True)
        # Stub method
        given().call(mock_store.get_data("key1")).returns({"val": "success"})

        assert mock_store.is_ready is True
        assert mock_store.get_data("key1") == {"val": "success"}

        verify().get(mock_store.is_ready).once()
        verify().call(mock_store.get_data("key1")).once()

    def test_protocol_runtime_checkability(self):
        """Verify that mock objects pass runtime protocol checks if the protocol is runtime_checkable."""
        mock_logger = tmock(Logger)

        # This is important for some libraries that use isinstance(obj, MyProtocol)
        assert isinstance(mock_logger, Logger)

    def test_integration_with_app(self):
        """Test a complete scenario using mocked protocols."""
        logger = tmock(Logger)
        store = tmock(DataStore)
        app = App(logger, store)

        # Stub behaviors
        given().get(store.is_ready).returns(True)
        given().call(store.get_data("user_1")).returns({"val": "Alice"})
        given().call(logger.log(any(str))).returns(None)

        # Act
        result = app.run("user_1")

        # Assert
        assert result == "Alice"
        verify().call(logger.log("Processed user_1")).once()

    def test_protocol_strictness(self):
        """Verify that protocol mocks are strict."""
        mock_logger = tmock(Logger)

        with pytest.raises(TMockUnexpectedCallError):
            mock_logger.log("unhandled")

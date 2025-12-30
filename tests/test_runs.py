import pytest

from tmock import CallArguments, any, tmock
from tmock.exceptions import TMockStubbingError
from tmock.stubbing_dsl import given


class TestRunsStubbing:
    """Tests for the .runs() stubbing behavior."""

    def test_runs_action_with_call_arguments(self):
        class Calculator:
            def add(self, a: int, b: int) -> int:
                return 0

        mock = tmock(Calculator)
        given(mock.add(any(int), any(int))).runs(lambda args: args.get_by_name("a") + args.get_by_name("b"))

        assert mock.add(3, 5) == 8
        assert mock.add(10, 20) == 30

    def test_runs_action_ignoring_arguments(self):
        class Service:
            def get_status(self) -> str:
                return ""

        mock = tmock(Service)
        given(mock.get_status()).runs(lambda _: "mocked status")

        assert mock.get_status() == "mocked status"

    def test_runs_with_side_effect(self):
        class EventEmitter:
            def emit(self, event: str) -> None:
                pass

        captured_events: list[str] = []
        mock = tmock(EventEmitter)
        given(mock.emit(any(str))).runs(lambda args: captured_events.append(args.get_by_name("event")))

        mock.emit("click")
        mock.emit("submit")

        assert captured_events == ["click", "submit"]

    def test_runs_validates_return_type(self):
        class Calculator:
            def multiply(self, a: int, b: int) -> int:
                return 0

        mock = tmock(Calculator)
        given(mock.multiply(any(int), any(int))).runs(
            lambda args: "not an int"  # Wrong return type
        )

        with pytest.raises(TMockStubbingError) as exc_info:
            mock.multiply(2, 3)

        assert "Invalid return type" in str(exc_info.value)

    def test_runs_with_complex_logic(self):
        class Cache:
            def get(self, key: str) -> str | None:
                return None

        fake_cache = {"user:1": "Alice", "user:2": "Bob"}
        mock = tmock(Cache)
        given(mock.get(any(str))).runs(lambda args: fake_cache.get(args.get_by_name("key")))

        assert mock.get("user:1") == "Alice"
        assert mock.get("user:2") == "Bob"
        assert mock.get("user:3") is None

    def test_runs_can_raise_exceptions(self):
        class Database:
            def query(self, sql: str) -> list[dict]:
                return []

        def execute_query(args: CallArguments) -> list[dict]:
            sql = args.get_by_name("sql")
            if "DROP" in sql:
                raise ValueError("DROP statements not allowed")
            return [{"result": "ok"}]

        mock = tmock(Database)
        given(mock.query(any(str))).runs(execute_query)

        assert mock.query("SELECT * FROM users") == [{"result": "ok"}]

        with pytest.raises(ValueError) as exc_info:
            mock.query("DROP TABLE users")

        assert "DROP statements not allowed" in str(exc_info.value)

    def test_runs_get_by_name_raises_for_unknown_argument(self):
        class Service:
            def process(self, data: str) -> str:
                return ""

        mock = tmock(Service)
        given(mock.process(any(str))).runs(
            lambda args: args.get_by_name("unknown")  # Wrong argument name
        )

        with pytest.raises(KeyError) as exc_info:
            mock.process("test")

        assert "No argument named 'unknown'" in str(exc_info.value)
        assert "Available: ['data']" in str(exc_info.value)

    def test_runs_with_multiple_stubs(self):
        class Formatter:
            def format(self, template: str, value: int) -> str:
                return ""

        mock = tmock(Formatter)
        given(mock.format("hex", any(int))).runs(lambda args: hex(args.get_by_name("value")))
        given(mock.format("bin", any(int))).runs(lambda args: bin(args.get_by_name("value")))

        assert mock.format("hex", 255) == "0xff"
        assert mock.format("bin", 5) == "0b101"
        assert mock.format("other", 10) is None

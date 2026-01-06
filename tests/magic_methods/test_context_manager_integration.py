from tmock import any, given, tmock, verify


class Connection:
    def execute(self, query: str) -> list[str]:
        return []


class Database:
    def connect(self) -> Connection:
        return Connection()

    def __enter__(self) -> Connection:
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class DataService:
    def __init__(self, db: Database):
        self.db = db

    def get_user_names(self) -> list[str]:
        with self.db as conn:
            return conn.execute("SELECT name FROM users")


class TestContextManagerIntegration:
    def test_service_using_mocked_database(self):
        """Test a service that depends on a context manager."""
        db_mock = tmock(Database)
        conn_mock = tmock(Connection)
        service = DataService(db_mock)

        # Stub the context manager flow
        given().call(db_mock.__enter__()).returns(conn_mock)
        given().call(conn_mock.execute("SELECT name FROM users")).returns(["Alice", "Bob"])
        given().call(db_mock.__exit__(None, None, None)).returns(None)

        # Act
        names = service.get_user_names()

        # Assert
        assert names == ["Alice", "Bob"]

        # Verify the protocol was followed
        verify().call(db_mock.__enter__()).once()
        verify().call(conn_mock.execute(any(str))).once()
        verify().call(db_mock.__exit__(None, None, None)).once()

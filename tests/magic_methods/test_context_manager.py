from typing import Any, Type

import pytest

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError


class Resource:
    def action(self) -> str:
        return "done"


class FileManager:
    def __enter__(self) -> Resource:
        return Resource()

    def __exit__(self, exc_type: Type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> bool | None:
        pass


class AsyncFileManager:
    async def __aenter__(self) -> Resource:
        return Resource()

    async def __aexit__(
        self, exc_type: Type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any
    ) -> bool | None:
        pass


class TestContextManagerStubbing:
    def test_raises_if_enter_not_stubbed(self):
        """Verify that entering a context manager without stubbing __enter__ raises UnexpectedCallError."""
        mock = tmock(FileManager)

        # __exit__ is stubbed, but __enter__ is not
        given().call(mock.__exit__(any(), any(), any())).returns(None)

        with pytest.raises(TMockUnexpectedCallError) as exc:
            with mock:
                pass
        assert "__enter__" in str(exc.value)

    def test_raises_if_exit_not_stubbed(self):
        """Verify that exiting a context manager without stubbing __exit__ raises UnexpectedCallError."""
        mock = tmock(FileManager)
        resource = tmock(Resource)

        given().call(mock.__enter__()).returns(resource)

        with pytest.raises(TMockUnexpectedCallError) as exc:
            with mock:
                pass
        assert "__exit__" in str(exc.value)

    def test_successful_flow_with_return_value(self):
        """Verify standard flow: enter returns a resource, used inside block, exit called with Nones."""
        manager_mock = tmock(FileManager)
        resource_mock = tmock(Resource)

        # Stubbing
        given().call(manager_mock.__enter__()).returns(resource_mock)
        given().call(resource_mock.action()).returns("mocked")
        given().call(manager_mock.__exit__(None, None, None)).returns(None)

        # Execution
        with manager_mock as res:
            assert res is resource_mock
            assert res.action() == "mocked"

        # Verification
        verify().call(manager_mock.__enter__()).once()
        verify().call(resource_mock.action()).once()
        verify().call(manager_mock.__exit__(None, None, None)).once()


class TestContextManagerExceptions:
    def test_exit_called_with_exception_info(self):
        """Verify __exit__ receives exception details when an error occurs in the block."""
        mock = tmock(FileManager)
        resource = tmock(Resource)

        given().call(mock.__enter__()).returns(resource)
        # Stub __exit__ to accept any arguments (since we can't easily predict exact traceback object)
        # and return False (don't suppress exception)
        given().call(mock.__exit__(any(), any(), any())).returns(False)

        with pytest.raises(ValueError, match="Boom"):
            with mock:
                raise ValueError("Boom")

        # Verify __exit__ was called.
        # Note: We can use matchers to be more specific about the exception type if needed.
        verify().call(mock.__exit__(any(type), any(ValueError), any())).once()

    def test_suppress_exception(self):
        """Verify that returning True from __exit__ suppresses the exception."""
        mock = tmock(FileManager)

        given().call(mock.__enter__()).returns(tmock(Resource))
        # Return True to suppress
        given().call(mock.__exit__(any(), any(), any())).returns(True)

        # Should NOT raise ValueError
        with mock:
            raise ValueError("Ignored error")

        verify().call(mock.__exit__(any(), any(), any())).once()


class TestAsyncContextManager:
    @pytest.mark.asyncio
    async def test_async_raises_if_not_stubbed(self):
        mock = tmock(AsyncFileManager)

        with pytest.raises(TMockUnexpectedCallError):
            async with mock:
                pass

    @pytest.mark.asyncio
    async def test_async_flow(self):
        manager_mock = tmock(AsyncFileManager)
        resource_mock = tmock(Resource)

        # Stub async methods
        given().call(manager_mock.__aenter__()).returns(resource_mock)
        given().call(manager_mock.__aexit__(None, None, None)).returns(None)

        async with manager_mock as res:
            assert res is resource_mock

        verify().call(manager_mock.__aenter__()).once()
        verify().call(manager_mock.__aexit__(None, None, None)).once()

    @pytest.mark.asyncio
    async def test_async_exception_handling(self):
        mock = tmock(AsyncFileManager)

        given().call(mock.__aenter__()).returns(tmock(Resource))
        given().call(mock.__aexit__(any(), any(), any())).returns(True)  # Suppress

        async with mock:
            raise RuntimeError("Async fail")

        verify().call(mock.__aexit__(any(type), any(RuntimeError), any())).once()


class TestTypeValidation:
    def test_enter_return_type_validation(self):
        """Verify that stubbing __enter__ with incorrect return type raises error."""
        mock = tmock(FileManager)

        # FileManager.__enter__ is annotated to return Resource.
        # Trying to return an int should fail stubbing validation.
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock.__enter__()).returns(123)

        assert "Invalid return type" in str(exc.value)

    def test_exit_return_type_validation(self):
        """Verify that stubbing __exit__ with incorrect return type raises error."""
        mock = tmock(FileManager)

        given().call(mock.__enter__()).returns(tmock(Resource))

        # FileManager.__exit__ returns bool | None.
        # Returning a string should fail.
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock.__exit__(None, None, None)).returns("not a bool")

        assert "Invalid return type" in str(exc.value)

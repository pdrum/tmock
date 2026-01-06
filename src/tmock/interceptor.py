from abc import ABC, abstractmethod
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum, auto
from inspect import Parameter, Signature
from typing import Any, Callable, TypeVar, overload

from typeguard import TypeCheckError, check_type

from tmock.call_record import (
    CallRecord,
    GetterCallRecord,
    MethodCallRecord,
    RecordedArgument,
    SetterCallRecord,
    pattern_matches_call,
)
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError, TMockVerificationError
from tmock.matchers.base import Matcher

T = TypeVar("T")


class DslType(Enum):
    STUBBING = auto()
    VERIFICATION = auto()


class DslPhase(Enum):
    NONE = auto()
    AWAITING_MOCK_INTERACTION = auto()
    AWAITING_TERMINAL = auto()


@dataclass
class BoundArgument:
    name: str
    value: Any
    annotation: Any


class CallArguments:
    """Container for accessing call arguments by name."""

    def __init__(self, arguments: tuple[RecordedArgument, ...]):
        self._args = {arg.name: arg.value for arg in arguments}

    @overload
    def get_by_name(self, name: str) -> Any: ...

    @overload
    def get_by_name(self, name: str, expected_type: type[T]) -> T: ...

    def get_by_name(self, name: str, expected_type: type[T] | None = None) -> Any:
        """Get argument value by name.

        Args:
            name: The parameter name.
            expected_type: Optional type for the return value. If provided,
                          the value is checked against this type at runtime.

        Returns:
            The argument value, typed as T if expected_type is provided.

        Raises:
            KeyError: If no argument with the given name exists.
            TypeError: If expected_type is provided and the value doesn't match.
        """
        if name not in self._args:
            raise KeyError(f"No argument named '{name}'. Available: {list(self._args.keys())}")
        value = self._args[name]
        if expected_type is not None:
            try:
                check_type(value, expected_type)
            except TypeCheckError:
                raise TypeError(f"Argument '{name}' has type {type(value).__name__}, expected {expected_type.__name__}")
        return value


class Stub(ABC):
    """Base class for all stub behaviors."""

    def __init__(self, call_record: CallRecord):
        self.call_record = call_record

    @abstractmethod
    def execute(self, arguments: CallArguments) -> Any:
        """Execute the stub behavior with the actual call arguments."""
        ...


class ReturnsStub(Stub):
    """Stub that returns a value."""

    def __init__(self, call_record: CallRecord, value: Any):
        super().__init__(call_record)
        self.value = value

    def execute(self, arguments: CallArguments) -> Any:
        return self.value


class RaisesStub(Stub):
    """Stub that raises an exception."""

    def __init__(self, call_record: CallRecord, exception: BaseException):
        super().__init__(call_record)
        self.exception = exception

    def execute(self, arguments: CallArguments) -> Any:
        raise self.exception


class RunsStub(Stub):
    """Stub that runs a custom action."""

    def __init__(self, call_record: CallRecord, action: Callable[[CallArguments], Any]):
        super().__init__(call_record)
        self.action = action

    def execute(self, arguments: CallArguments) -> Any:
        return self.action(arguments)


class Interceptor(ABC):
    """Base class for all interceptors (methods, getters, setters)."""

    def __init__(self, name: str, signature: Signature, class_name: str):
        self._name = name
        self._signature = signature
        self._class_name = class_name
        self._calls: list[CallRecord] = []
        self._stubs: list[Stub] = []

    @abstractmethod
    def _create_record(self, arguments: tuple[RecordedArgument, ...]) -> CallRecord:
        """Create the appropriate CallRecord subclass for this interceptor type."""
        raise NotImplementedError

    def pop_last_call(self) -> CallRecord:
        return self._calls.pop()

    def count_matching_calls(self, expected: CallRecord) -> int:
        return sum(1 for call in self._calls if pattern_matches_call(expected, call))

    def add_stub(self, stub: Stub) -> None:
        """Add a stub to this method."""
        self._stubs.append(stub)

    def reset_interactions(self) -> None:
        """Clear all recorded calls."""
        self._calls.clear()

    def reset_behaviors(self) -> None:
        """Clear all stubs."""
        self._stubs.clear()

    def reset(self) -> None:
        """Reset both interactions and behaviors."""
        self.reset_interactions()
        self.reset_behaviors()

    def validate_return_type(self, value: Any) -> None:
        """Validate that a value matches the method's return type annotation."""
        self._validate_return_type(value)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        dsl = get_dsl_state()
        dsl.check_no_pending_terminal()
        bound_args = self._bind_arguments(args, kwargs)
        self._validate_arg_types(bound_args)
        arguments = tuple(RecordedArgument(ba.name, ba.value) for ba in bound_args)
        record = self._create_record(arguments)

        if dsl.is_awaiting_mock_interaction():
            dsl.record_dsl_call(self, record)
            return None

        self._calls.append(record)
        return self._find_stub(record)

    def _find_stub(self, record: CallRecord) -> Any:
        # Iterate in reverse so later stubs take precedence
        for stub in reversed(self._stubs):
            if pattern_matches_call(stub.call_record, record):
                arguments = CallArguments(record.arguments)
                return stub.execute(arguments)
        raise TMockUnexpectedCallError(f"No matching behavior defined on {self._class_name} for {record.format_call()}")

    def _bind_arguments(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> list[BoundArgument]:
        try:
            bound = self._signature.bind(*args, **kwargs)
            bound.apply_defaults()
        except TypeError as e:
            raise TMockStubbingError(f"Invalid args passed to {self._name} => {e}")

        result = []
        for param_name, value in bound.arguments.items():
            param = self._signature.parameters[param_name]
            result.append(BoundArgument(param_name, value, param.annotation))
        return result

    def _validate_arg_types(self, bound_args: list[BoundArgument]) -> None:
        for arg in bound_args:
            if arg.annotation is Parameter.empty:
                continue
            if isinstance(arg.value, Matcher):
                continue
            try:
                check_type(arg.value, arg.annotation)
            except TypeCheckError:
                raise TMockStubbingError(
                    f"Invalid type for argument '{arg.name}' of {self._name}, expected {arg.annotation}, "
                    f"got {type(arg.value).__name__}"
                )

    def _validate_return_type(self, value: Any) -> None:
        return_annotation = self._signature.return_annotation
        if return_annotation is Signature.empty:
            return
        try:
            check_type(value, return_annotation)
        except TypeCheckError:
            raise TMockStubbingError(
                f"Invalid return type for {self._name}, expected {return_annotation}, got {type(value).__name__}"
            )


class MethodInterceptor(Interceptor):
    """Interceptor for method calls."""

    def __init__(self, name: str, signature: Signature, class_name: str, is_async: bool = False):
        super().__init__(name, signature, class_name)
        self._is_async = is_async

    def _create_record(self, arguments: tuple[RecordedArgument, ...]) -> CallRecord:
        return MethodCallRecord(self._name, arguments)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        dsl = get_dsl_state()
        dsl.check_no_pending_terminal()
        bound_args = self._bind_arguments(args, kwargs)
        self._validate_arg_types(bound_args)
        arguments = tuple(RecordedArgument(ba.name, ba.value) for ba in bound_args)
        record = self._create_record(arguments)

        if dsl.is_awaiting_mock_interaction():
            dsl.record_dsl_call(self, record)
            return None

        # Async methods must return a coroutine object that can be awaited.
        # We dispatch to _async_call (which is async def) to get this behavior.
        if self._is_async:
            return self._async_call(record)
        return self._sync_call(record)

    def _sync_call(self, record: CallRecord) -> Any:
        self._calls.append(record)
        return self._find_stub(record)

    async def _async_call(self, record: CallRecord) -> Any:
        # The 'async def' keyword makes this return a coroutine object.
        # The logic is identical to _sync_call, but wrapping it in async def
        # means callers must 'await' the result, matching real async method behavior.
        self._calls.append(record)
        return self._find_stub(record)


class GetterInterceptor(Interceptor):
    """Interceptor for property getter access."""

    def _create_record(self, arguments: tuple[RecordedArgument, ...]) -> CallRecord:
        return GetterCallRecord(self._name, arguments)


class SetterInterceptor(Interceptor):
    """Interceptor for property setter access."""

    def _create_record(self, arguments: tuple[RecordedArgument, ...]) -> CallRecord:
        return SetterCallRecord(self._name, arguments)


class DslState:
    def __init__(self) -> None:
        self.phase: DslPhase = DslPhase.NONE
        self.type: DslType | None = None
        self.interceptor: Interceptor | None = None
        self.record: CallRecord | None = None

    def enter_dsl_mode(self, dsl_type: DslType) -> None:
        """Called by given() or verify() to enter DSL mode."""
        if self.phase != DslPhase.NONE:
            raise self._incomplete_error()
        self.phase = DslPhase.AWAITING_MOCK_INTERACTION
        self.type = dsl_type

    def record_dsl_call(self, interceptor: Interceptor, record: CallRecord) -> None:
        """Called by mock method when in DSL mode to record the pattern."""
        self.phase = DslPhase.AWAITING_TERMINAL
        self.interceptor = interceptor
        self.record = record

    def begin_terminal(self) -> tuple[Interceptor, CallRecord]:
        """Called by .call() to get interceptor and record."""
        if self.phase != DslPhase.AWAITING_TERMINAL:
            if self.phase == DslPhase.NONE:
                raise TMockStubbingError("Must call given() or verify() before .call().")
            elif self.phase == DslPhase.AWAITING_MOCK_INTERACTION:
                raise TMockStubbingError(f"{self._dsl_name()}() was called but no mock interaction occurred.")
        assert self.interceptor is not None and self.record is not None
        return self.interceptor, self.record

    def complete(self) -> None:
        """Called by terminal methods (.returns(), .times(), etc.) to reset state."""
        self.phase = DslPhase.NONE
        self.type = None
        self.interceptor = None
        self.record = None

    def check_no_pending_terminal(self) -> None:
        """Raise if there's an incomplete DSL operation awaiting terminal method."""
        if self.phase == DslPhase.AWAITING_TERMINAL:
            raise self._incomplete_error()

    def is_awaiting_mock_interaction(self) -> bool:
        return self.phase == DslPhase.AWAITING_MOCK_INTERACTION

    def reset(self) -> None:
        """Reset the state completely (for test cleanup)."""
        self.phase = DslPhase.NONE
        self.type = None
        self.interceptor = None
        self.record = None

    def _dsl_name(self) -> str:
        if self.type == DslType.STUBBING:
            return "given"
        elif self.type == DslType.VERIFICATION:
            return "verify"
        raise ValueError(f"Unknown DSL type: {self.type}")

    def _incomplete_error(self) -> Exception:
        if self.phase == DslPhase.AWAITING_MOCK_INTERACTION:
            return TMockStubbingError(
                f"Incomplete DSL: {self._dsl_name()}() was called but no mock interaction occurred."
            )
        elif self.phase == DslPhase.AWAITING_TERMINAL:
            record_str = self.record.format_call() if self.record else "unknown"
            if self.type == DslType.STUBBING:
                return TMockStubbingError(
                    f"Incomplete stub: given().call({record_str}) was never completed. "
                    f"Did you forget to call .returns(), .raises(), or .runs()?"
                )
            else:
                return TMockVerificationError(
                    f"Incomplete verification: verify().call({record_str}) was never completed. "
                    f"Did you forget to call .times(), .once(), .never(), .called(), .at_least(), or .at_most()?"
                )
        return TMockStubbingError("Unknown DSL state error.")


_dsl_state: ContextVar[DslState | None] = ContextVar("dsl_state", default=None)


def get_dsl_state() -> DslState:
    """Get the current DSL state, creating one if needed."""
    state = _dsl_state.get()
    if state is None:
        state = DslState()
        _dsl_state.set(state)
    return state


def reset_dsl_state() -> None:
    """Reset the DSL state (for test cleanup)."""
    state = _dsl_state.get()
    if state is not None:
        state.reset()

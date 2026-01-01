# tmock

A type-safe mock library for Python with full IDE autocomplete support.

## Development

- Use type hints everywhere (mypy strict)
- Run `pre-commit run --all-files` before committing
- Tests: `pytest`

## Directory Structure

```
src/tmock/
├── __init__.py          # Public API exports (tmock, given, verify, any, reset, etc.)
├── mock_generator.py    # tmock() function - creates mock instances
├── class_schema.py      # Introspects classes for fields/methods/properties
├── call_record.py       # CallRecord hierarchy (Method/Getter/Setter variants)
├── interceptor.py       # Interceptor hierarchy, Stub classes, DSL state management
├── field_ref.py         # FieldRef - represents a field access for stubbing/verification
├── stubbing_dsl.py      # given().call/get/set().returns() DSL
├── verification_dsl.py  # verify().call/get/set().once/times/never() DSL
├── reset.py             # reset(), reset_interactions(), reset_behaviors()
├── matchers/            # Argument matchers (any(), etc.)
└── exceptions.py        # TMockStubbingError, TMockUnexpectedCallError, TMockVerificationError

tests/
├── method_dsl/          # Tests for method stubbing/verification
├── field_dsl/           # Tests for getter/setter stubbing/verification
├── error_messages/      # Tests for error message formatting
└── matchers/            # Tests for argument matchers
```

## DSL Patterns

```python
# Create a mock
mock = tmock(MyClass)
mock = tmock(MyClass, extra_fields=["name", "age"])  # For fields only in __init__

# Stub methods
given().call(mock.method(arg1, arg2)).returns(value)
given().call(mock.method(any(int), "specific")).returns(value)

# Stub field getters/setters
given().get(mock.field).returns(value)
given().set(mock.field, value).returns(None)
given().set(mock.field, any(str)).returns(None)

# Verify calls
verify().call(mock.method(arg1, arg2)).once()
verify().call(mock.method(any())).times(3)
verify().get(mock.field).called()
verify().set(mock.field, value).never()
verify().call(mock.method(any())).at_least(2)
verify().call(mock.method(any())).at_most(5)
```

## Architecture

**Interceptor hierarchy** (each owns its calls, stubs, signature):
```
Interceptor (ABC)
├── MethodInterceptor  → for method calls
├── GetterInterceptor  → for field getter access
└── SetterInterceptor  → for field setter access
```

**CallRecord hierarchy** (each formats its own error messages):
```
CallRecord (ABC)
├── MethodCallRecord   → formats: method(a=1, b=2)
├── GetterCallRecord   → formats: get field
└── SetterCallRecord   → formats: set field = 'value'
```

## Key Concepts

- **Interceptor**: Base class for stateful interceptors. Holds calls, stubs, and signature.
- **FieldRef**: Returned when accessing a field in DSL mode. Contains references to getter/setter interceptors.
- **FieldSchema**: Metadata for a field including getter/setter signatures and source (PROPERTY, ANNOTATION, DATACLASS, PYDANTIC, EXTRA).
- **extra_fields**: For classes with fields only defined in `__init__` (not discoverable). These have `Any` type. Typed annotations take priority over extra_fields.
- **DSL State**: Uses ContextVar for async-safe call capture. `given()`/`verify()` set state, field/method access captures the interaction.
- **Reset functions**: `reset(mock)` clears all state, `reset_interactions(mock)` clears calls only, `reset_behaviors(mock)` clears stubs only.

## Design Principles

- Each interceptor owns its method's state (calls, stubs, signature)
- Inheritance over conditionals - each interceptor/record type handles its own formatting
- No central "bag of state" - prefer OO design with clear responsibilities
- DSL should provide full IDE autocomplete where possible
- Type checking at stub time, not call time

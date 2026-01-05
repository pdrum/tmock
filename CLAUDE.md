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

## Patching (tpatch)

The `tpatch` class provides stdlib-backed patching with typed interceptors. It wraps `unittest.mock.patch` internally but returns tmock interceptors for use with the `given()`/`verify()` DSL.

### API

```python
from tmock import tpatch, given, verify

# Functions (supports from...import)
with tpatch.function("myapp.service.get_user") as mock:
    given().call(mock(1)).returns(User(id=1))

# Instance methods
with tpatch.method(MyClass, "save") as mock:
    given().call(mock(any(User))).returns(True)

# Static methods
with tpatch.staticmethod(MyClass, "create") as mock:
    given().call(mock("data")).returns(instance)

# Class methods
with tpatch.classmethod(MyClass, "from_env") as mock:
    given().call(mock()).returns(Config())

# Instance fields (property, dataclass, pydantic, annotation)
with tpatch.field(Person, "name") as field:
    given().get(field).returns("Alice")
    given().set(field, "Bob").returns(None)

# Class variables
with tpatch.class_var(MyClass, "DEFAULT_TIMEOUT") as field:
    given().get(field).returns(30)

# Module variables
with tpatch.module_var(config_module, "DEBUG") as field:
    given().get(field).returns(True)
```

### Design

Each method is explicit about what it patches. Validation ensures the user called the correct method:

| Method | Patches | Validates | Type info from |
|--------|---------|-----------|----------------|
| `tpatch.function(path)` | Module functions, from...import | `callable(attr)` | `inspect.signature` |
| `tpatch.method(cls, name)` | Instance methods | has `self` param | `inspect.signature` |
| `tpatch.staticmethod(cls, name)` | Static methods | `isinstance(attr, staticmethod)` | `inspect.signature` |
| `tpatch.classmethod(cls, name)` | Class methods | `isinstance(attr, classmethod)` | `inspect.signature` |
| `tpatch.field(cls, name)` | Instance fields | in `FieldDiscovery` or `property` | `FieldDiscovery` |
| `tpatch.class_var(cls, name)` | Class variables | not callable, not descriptor | `ClassVar` annotation or `Any` |
| `tpatch.module_var(module, name)` | Module variables | not callable | Module annotation or `Any` |

### Implementation Notes

- All patching delegated to `unittest.mock.patch` / `unittest.mock.patch.object`
- tmock builds the appropriate interceptor and passes it as the `new` argument
- For methods with `self`/`cls`, a wrapper strips the first argument
- For fields/variables, a `_FieldDescriptor` is installed to intercept get/set
- Type hints extracted from:
  - `FieldDiscovery` for instance fields (property, dataclass, pydantic, annotation)
  - `typing.get_type_hints()` + `ClassVar` unwrapping for class variables
  - `typing.get_type_hints()` for module variables
  - Falls back to `Any` if no type info available

### File Structure

```
src/tmock/
├── tpatch.py            # tpatch class with function/method/staticmethod/classmethod/field/class_var/module_var
└── ...
```

### Error Messages

When the wrong method is used, helpful errors guide to the correct one:

```python
with tpatch.method(MyClass, "static_func"):
    ...
# TMockPatchingError: 'static_func' is a staticmethod. Use tpatch.staticmethod().

with tpatch.field(MyClass, "CLASS_CONST"):
    ...
# TMockPatchingError: 'CLASS_CONST' is not a field on 'MyClass'. Use tpatch.class_var().
```

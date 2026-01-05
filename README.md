# tmock

**Type-safe mocking for modern Python.**

`tmock` is a mocking library designed to keep your tests aligned with your actual code. It prioritizes type safety and signature adherence over the infinite flexibility of standard "magic" mocks.

## Why tmock?

The standard library's `unittest.mock` is incredibly flexible. However, that flexibility can sometimes be a liability. A `MagicMock` will happily accept arguments that don't exist in your function signature, or types that would cause your real code to crash.

**The Trade-off:**

* **unittest.mock:** Optimizes for ease of setup. If you change a method signature in your code, your old tests often keep passing silently, only for the code to fail in production.
* **tmock:** Optimizes for correctness. It reads the type hints and signatures of your actual classes. If you try to stub a mock with the wrong arguments or types, the test fails immediately.

### Scenario: The Silent Drift

Imagine you refactor a method from `save(data)` to `save(data, should_commit)`.

1. **With Standard Mocks:** Your existing test calls `mock.save(data)`. The mock accepts it without complaint. The test passes, but it's no longer testing the reality of your API.
2. **With tmock:** When you run the test, `tmock` validates the call against the new signature. It notices discrepancies immediately, forcing you to update your test to match the new code structure.

## Key Features

### 1. Runtime Type Validation

This is the core differentiator of `tmock`. It doesn't just count arguments; it checks their types against your source code's annotations.

If your method is defined as:

```python
def update_score(self, user_id: int, score: float) -> bool: ...

```

Trying to stub it with incorrect types raises an error *before the test even runs*:

```python
# RAISES ERROR: TypeError: Argument 'user_id' expected int, got str
given().call(mock.update_score("user_123", 95.5)).returns(True)

```

### 2. Better IDE Support

Because `tmock` mirrors the structure of your class, it plays much nicer with your editor than dynamic mocks. You get better autocompletion and static analysis support, making it easier to write tests without constantly flipping back to the source file to remember argument names.

### 3. Native Property & Field Support

Mocking properties or data attributes usually requires verbose `__setattr__` patching. `tmock` handles them natively via its DSL, supporting getters, setters, Dataclasses, and Pydantic models out of the box.

---

## Installation

`tmock` is currently in late-stage development and is **coming soon to PyPI**.

```bash
# Coming soon
pip install tmock

```

## Usage Guide

### Creating a Mock

The entry point is simple. Pass your class to `tmock` to create a strict proxy.

```python
from tmock import tmock, given, verify, any
from my_app import Database

db = tmock(Database)

```

### Stubbing (The `given` DSL)

Stubbing is done explicitly. This allows `tmock` to validate that what you are mocking is actually possible.

```python
# Simple return value
given().call(db.get_user(123)).returns({"name": "Alice"})

# Using Matchers for loose constraints
given().call(db.save_record(any(dict))).returns(True)

# Raising exceptions to test error handling
given().call(db.connect()).raises(ConnectionError("Timeout"))

# Dynamic responses
given().call(db.calculate(10)).runs(lambda args: args.get_by_name("val") * 2)

```

### Verification (The `verify` DSL)

Assert that specific interactions occurred.

```python
# Verify exact call count
verify().call(db.save_record(any())).once()

# Verify something never happened
verify().call(db.delete_all()).never()

# Verify with specific counts
verify().call(db.connect()).times(3)

```

### Working with Fields and Properties

Stub and verify state changes on attributes, properties, or Pydantic fields.

```python
# Stubbing a value retrieval
given().get(db.is_connected).returns(True)

# Stubbing a value assignment
given().set(db.timeout, 5000).returns(None)

# Verifying a setter was called
verify().set(db.timeout, 5000).once()

```

## Patching (`tpatch`)

When you need to swap out objects internally used by other modules, use `tpatch`. It wraps `unittest.mock.patch` but creates a typed `tmock` interceptor instead of a generic mock.

The API forces you to be explicit about *what* you are patching (Method vs. Function vs. Field), which prevents common patching errors.

```python
from tmock import tpatch, given

# Patching an instance method
with tpatch.method(UserService, "get_current_user") as mock:
    given().call(mock()).returns(admin_user)
    
# Patching a module-level function
with tpatch.function("my_module.external_api_call") as mock:
    given().call(mock()).returns(200)

# Patching a class variable
with tpatch.class_var(Config, "MAX_RETRIES") as field:
    given().get(field).returns(1)

```

## Async Support

`tmock` natively handles `async`/`await`. You stub async methods exactly the same way as synchronous ones; `tmock` handles the coroutine wrapping for you.

```python
# Stubbing an async method
given().call(api_client.fetch_data()).returns(data)

# The mock is automatically awaitable
result = await api_client.fetch_data() 

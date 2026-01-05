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

## Quick Demo

Here's a realistic example: testing a `NotificationService` that depends on an `EmailClient` and uses a module-level config.

**The production code:**

```python
# notification_service.py
from myapp.config import MAX_BATCH_SIZE
from myapp.email import EmailClient

class NotificationService:
    def __init__(self, email_client: EmailClient):
        self.client = email_client

    def notify_users(self, user_ids: list[int], message: str) -> int:
        """Send notifications in batches. Returns count of successful sends."""
        sent = 0
        for i in range(0, len(user_ids), MAX_BATCH_SIZE):
            batch = user_ids[i:i + MAX_BATCH_SIZE]
            for user_id in batch:
                if self.client.send(user_id, message):
                    sent += 1
        return sent
```

**Testing with mocks** — Use `tmock()` when you control the dependency and pass it in (dependency injection):

```python
from tmock import tmock, given, verify, any

def test_notify_users_returns_success_count():
    # Create a type-safe mock of the dependency
    client = tmock(EmailClient)

    # Stub the send method - first call succeeds, second fails
    given().call(client.send(1, "Hello")).returns(True)
    given().call(client.send(2, "Hello")).returns(False)

    # Inject the mock and test
    service = NotificationService(client)
    result = service.notify_users([1, 2], "Hello")

    assert result == 1  # Only one succeeded
    verify().call(client.send(any(int), "Hello")).times(2)
```

**Testing with patches** — Use `tpatch` when you need to replace something you don't control, like a module variable or a function called internally:

```python
from tmock import tpatch

def test_notify_users_respects_batch_size():
    client = tmock(EmailClient)
    given().call(client.send(any(int), any(str))).returns(True)

    # Patch the module variable to force smaller batches
    with tpatch.module_var("path.to.notification_service.MAX_BATCH_SIZE", 2):
        service = NotificationService(client)
        service.notify_users([1, 2, 3, 4, 5], "Hi")

        # Verify all 5 emails were sent despite small batch size
        verify().call(client.send(any(int), "Hi")).times(5)
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

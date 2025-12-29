# tmock

A type-safe mock library for Python with full IDE autocomplete support.

## Development

- Use type hints everywhere (mypy strict)
- Run `pre-commit run --all-files` before committing
- Tests: `pytest`

## Architecture

- **MethodInterceptor**: Stateful object representing a mocked method. Holds its own calls, stubs, and signature.
- **tmock()**: Creates mock instances. Caches interceptors per method for stable identity.
- **Stubbing DSL**: `given(mock.method(...)).returns(value)` - uses ContextVar for async-safe call capture.

## Design Principles

- Each interceptor owns its method's state (calls, stubs, signature)
- No central "bag of state" - prefer OO design with clear responsibilities
- DSL should provide full IDE autocomplete where possible
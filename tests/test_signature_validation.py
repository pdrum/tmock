import pytest

from tmock import tmock
from tmock.exceptions import TMockStubbingError
from tmock.stubbing_dsl import given


class TestArgumentTypeValidation:
    @pytest.mark.parametrize(
        "value",
        [
            "string",
            3.14,
            [],
            {},
        ],
    )
    def test_invalid_arg_type_raises(self, value):
        class SampleClass:
            def foo(self, x: int) -> int:
                return x

        mock = tmock(SampleClass)
        with pytest.raises(TMockStubbingError, match="Invalid type for argument"):
            mock.foo(value)

    def test_invalid_arg_type_with_multiple_params(self):
        class SampleClass:
            def foo(self, a: int, b: str) -> int:
                return 0

        mock = tmock(SampleClass)
        with pytest.raises(TMockStubbingError, match="Invalid type for argument 'b'"):
            mock.foo(1, 123)

    def test_none_when_not_optional_raises(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return x

        mock = tmock(SampleClass)
        with pytest.raises(TMockStubbingError):
            mock.foo(None)

    def test_none_allowed_for_optional(self):
        class SampleClass:
            def foo(self, x: int | None) -> int:
                return 0

        mock = tmock(SampleClass)
        mock.foo(None)  # Should not raise

    def test_list_element_type_validated(self):
        class SampleClass:
            def foo(self, items: list[int]) -> int:
                return 0

        mock = tmock(SampleClass)
        mock.foo([1, 2, 3])  # Valid
        with pytest.raises(TMockStubbingError):
            mock.foo(["a", "b"])  # Invalid element type

    def test_dict_type_validated(self):
        class SampleClass:
            def foo(self, data: dict[str, int]) -> int:
                return 0

        mock = tmock(SampleClass)
        mock.foo({"a": 1})  # Valid
        with pytest.raises(TMockStubbingError):
            mock.foo({1: "wrong"})  # Invalid key and value types


class TestArgumentCountValidation:
    def test_missing_required_arg_raises(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return x

        mock = tmock(SampleClass)
        with pytest.raises(TMockStubbingError, match="Invalid args"):
            mock.foo()

    def test_too_many_args_raises(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return x

        mock = tmock(SampleClass)
        with pytest.raises(TMockStubbingError, match="Invalid args"):
            mock.foo(1, 2, 3)

    def test_unexpected_kwarg_raises(self):
        class SampleClass:
            def foo(self, x: int) -> int:
                return x

        mock = tmock(SampleClass)
        with pytest.raises(TMockStubbingError, match="Invalid args"):
            mock.foo(x=1, y=2)

    def test_default_args_not_required(self):
        class SampleClass:
            def foo(self, x: int, y: int = 10) -> int:
                return x + y

        mock = tmock(SampleClass)
        mock.foo(5)  # Should not raise


class TestReturnTypeValidation:
    @pytest.mark.parametrize(
        "return_value",
        [
            "string",
            3.14,
            [],
            None,
        ],
    )
    def test_invalid_return_type_raises(self, return_value):
        class SampleClass:
            def foo(self) -> int:
                return 0

        mock = tmock(SampleClass)
        with pytest.raises(TMockStubbingError, match="Invalid return type"):
            given(mock.foo()).returns(return_value)

    def test_none_allowed_for_optional_return(self):
        class SampleClass:
            def foo(self) -> int | None:
                return 0

        mock = tmock(SampleClass)
        given(mock.foo()).returns(None)  # Should not raise

    def test_list_return_type_validated(self):
        class SampleClass:
            def foo(self) -> list[int]:
                return []

        mock = tmock(SampleClass)
        given(mock.foo()).returns([1, 2, 3])  # Valid
        with pytest.raises(TMockStubbingError):
            given(mock.foo()).returns(["a", "b"])

    def test_no_return_annotation_allows_any(self):
        class SampleClass:
            def foo(self):
                pass

        mock = tmock(SampleClass)
        given(mock.foo()).returns("anything")  # Should not raise
        given(mock.foo()).returns(123)  # Should not raise


class TestGivenWithoutMockCall:
    def test_given_without_mock_call_raises(self):
        with pytest.raises(TMockStubbingError, match="given\\(\\) expects a mock method call"):
            given(42)

    def test_given_with_none_raises(self):
        with pytest.raises(TMockStubbingError, match="given\\(\\) expects a mock method call"):
            given(None)

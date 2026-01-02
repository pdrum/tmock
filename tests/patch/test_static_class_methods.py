"""Tests for patching static methods and class methods."""

import pytest

from tests.patch.sample_class import Calculator
from tmock import CallArguments, any, given, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError
from tmock.patch import patch


class TestStaticMethodPatching:
    def test_patch_static_method_with_stub(self):
        with patch(Calculator).add as mock_add:
            given().call(mock_add(1, 2)).returns(100)
            assert Calculator.add(1, 2) == 100

        # After context, original is restored
        assert Calculator.add(1, 2) == 3

    def test_patch_static_method_without_stub_raises(self):
        with patch(Calculator).add:
            with pytest.raises(TMockUnexpectedCallError):
                Calculator.add(1, 2)

    def test_patch_static_method_with_different_args(self):
        with patch(Calculator).add as mock_add:
            given().call(mock_add(1, 2)).returns(10)
            given().call(mock_add(3, 4)).returns(20)

            assert Calculator.add(1, 2) == 10
            assert Calculator.add(3, 4) == 20

    def test_patch_static_method_with_matcher(self):
        with patch(Calculator).add as mock_add:
            given().call(mock_add(any(int), any(int))).returns(999)

            assert Calculator.add(1, 2) == 999
            assert Calculator.add(100, 200) == 999

    def test_patch_static_method_verify_calls(self):
        with patch(Calculator).greet as mock_greet:
            given().call(mock_greet(any(str))).returns("Hi!")

            Calculator.greet("Alice")
            Calculator.greet("Bob")
            Calculator.greet("Alice")

            verify().call(mock_greet("Alice")).times(2)
            verify().call(mock_greet("Bob")).once()

    def test_patch_static_method_raises(self):
        with patch(Calculator).add as mock_add:
            given().call(mock_add(any(int), 0)).raises(ZeroDivisionError("cannot add zero"))

            with pytest.raises(ZeroDivisionError):
                Calculator.add(10, 0)

    def test_patch_static_method_runs(self):
        call_log: list[tuple[int, int]] = []

        def log_and_return(args: CallArguments) -> int:
            a = args.get_by_name("a", int)
            b = args.get_by_name("b", int)
            call_log.append((a, b))
            return a * b

        with patch(Calculator).add as mock_add:
            given().call(mock_add(any(int), any(int))).runs(log_and_return)

            assert Calculator.add(3, 4) == 12
            assert Calculator.add(5, 6) == 30

        assert call_log == [(3, 4), (5, 6)]

    def test_patch_static_method_type_validation(self):
        with patch(Calculator).add as mock_add:
            with pytest.raises(TMockStubbingError) as exc_info:
                given().call(mock_add("not an int", 2)).returns(0)

            assert "Invalid type for argument 'a'" in str(exc_info.value)


class TestClassMethodPatching:
    def test_patch_class_method_with_stub(self):
        with patch(Calculator).multiply as mock_multiply:
            given().call(mock_multiply(5)).returns(100)
            assert Calculator.multiply(5) == 100

        # After context, original is restored
        assert Calculator.multiply(5) == 10  # 5 * 2

    def test_patch_class_method_without_stub_raises(self):
        with patch(Calculator).multiply:
            with pytest.raises(TMockUnexpectedCallError):
                Calculator.multiply(5)

    def test_patch_class_method_with_different_args(self):
        with patch(Calculator).multiply as mock_multiply:
            given().call(mock_multiply(5)).returns(50)
            given().call(mock_multiply(10)).returns(200)

            assert Calculator.multiply(5) == 50
            assert Calculator.multiply(10) == 200

    def test_patch_class_method_with_matcher(self):
        with patch(Calculator).multiply as mock_multiply:
            given().call(mock_multiply(any(int))).returns(999)

            assert Calculator.multiply(1) == 999
            assert Calculator.multiply(100) == 999

    def test_patch_class_method_no_args(self):
        with patch(Calculator).get_class_name as mock_get_name:
            given().call(mock_get_name()).returns("MockedClass")
            assert Calculator.get_class_name() == "MockedClass"

        assert Calculator.get_class_name() == "Calculator"

    def test_patch_class_method_verify_calls(self):
        with patch(Calculator).multiply as mock_multiply:
            given().call(mock_multiply(any(int))).returns(0)

            Calculator.multiply(5)
            Calculator.multiply(10)
            Calculator.multiply(5)

            verify().call(mock_multiply(5)).times(2)
            verify().call(mock_multiply(10)).once()

    def test_patch_class_method_raises(self):
        with patch(Calculator).multiply as mock_multiply:
            given().call(mock_multiply(0)).raises(ValueError("cannot multiply zero"))

            with pytest.raises(ValueError):
                Calculator.multiply(0)

    def test_patch_class_method_runs(self):
        call_log: list[int] = []

        def log_and_return(args: CallArguments) -> int:
            value = args.get_by_name("value", int)
            call_log.append(value)
            return value * 10

        with patch(Calculator).multiply as mock_multiply:
            given().call(mock_multiply(any(int))).runs(log_and_return)

            assert Calculator.multiply(3) == 30
            assert Calculator.multiply(5) == 50

        assert call_log == [3, 5]

    def test_patch_class_method_type_validation(self):
        with patch(Calculator).multiply as mock_multiply:
            with pytest.raises(TMockStubbingError) as exc_info:
                given().call(mock_multiply("not an int")).returns(0)

            assert "Invalid type for argument 'value'" in str(exc_info.value)


class TestStaticMethodPatchingAsync:
    @pytest.mark.asyncio
    async def test_patch_async_static_method(self):
        with patch(Calculator).async_compute as mock_compute:
            given().call(mock_compute(5)).returns(100)
            result = await Calculator.async_compute(5)
            assert result == 100

        # Original restored
        result = await Calculator.async_compute(5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_patch_async_static_method_with_matcher(self):
        with patch(Calculator).async_compute as mock_compute:
            given().call(mock_compute(any(int))).returns(999)

            result1 = await Calculator.async_compute(1)
            result2 = await Calculator.async_compute(100)

            assert result1 == 999
            assert result2 == 999


class TestClassMethodPatchingAsync:
    @pytest.mark.asyncio
    async def test_patch_async_class_method(self):
        with patch(Calculator).async_class_method as mock_method:
            given().call(mock_method(42)).returns("mocked")
            result = await Calculator.async_class_method(42)
            assert result == "mocked"

        # Original restored
        result = await Calculator.async_class_method(42)
        assert result == "Calculator: 42"

    @pytest.mark.asyncio
    async def test_patch_async_class_method_raises(self):
        with patch(Calculator).async_class_method as mock_method:
            given().call(mock_method(any(int))).raises(ConnectionError("network error"))

            with pytest.raises(ConnectionError):
                await Calculator.async_class_method(5)


class TestPatchErrors:
    def test_patch_nonexistent_method_raises(self):
        with pytest.raises(AttributeError) as exc_info:
            patch(Calculator).nonexistent

        assert "has no attribute 'nonexistent'" in str(exc_info.value)

    def test_patch_non_module_or_class_raises(self):
        with pytest.raises(TypeError) as exc_info:
            patch("not a module or class")  # type: ignore

        assert "requires a module or class" in str(exc_info.value)

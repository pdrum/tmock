import pytest

from tests.patch.sample_class import Counter
from tmock import CallArguments, any, given, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError
from tmock.patch import patch


class TestInstanceMethodPatching:
    def test_patch_instance_method_with_stub(self):
        with patch(Counter).increment as mock_increment:
            given().call(mock_increment(10)).returns(100)

            counter = Counter(5)
            assert counter.increment(10) == 100

        # After context, original is restored
        counter = Counter(5)
        assert counter.increment(10) == 15

    def test_patch_instance_method_without_stub_raises(self):
        with patch(Counter).increment:
            counter = Counter(5)
            with pytest.raises(TMockUnexpectedCallError):
                counter.increment(10)

    def test_patch_instance_method_with_different_args(self):
        with patch(Counter).increment as mock_increment:
            given().call(mock_increment(10)).returns(100)
            given().call(mock_increment(20)).returns(200)

            counter = Counter(0)
            assert counter.increment(10) == 100
            assert counter.increment(20) == 200

    def test_patch_instance_method_with_matcher(self):
        with patch(Counter).increment as mock_increment:
            given().call(mock_increment(any(int))).returns(999)

            counter = Counter(0)
            assert counter.increment(1) == 999
            assert counter.increment(100) == 999

    def test_patch_instance_method_no_args(self):
        with patch(Counter).get_value as mock_get_value:
            given().call(mock_get_value()).returns(42)

            counter = Counter(10)
            assert counter.get_value() == 42

        # Original restored
        counter = Counter(10)
        assert counter.get_value() == 10

    def test_patch_instance_method_verify_calls(self):
        with patch(Counter).increment as mock_increment:
            given().call(mock_increment(any(int))).returns(0)

            counter = Counter(0)
            counter.increment(5)
            counter.increment(10)
            counter.increment(5)

            verify().call(mock_increment(5)).times(2)
            verify().call(mock_increment(10)).once()

    def test_patch_instance_method_multiple_instances(self):
        """Patching affects all instances of the class."""
        with patch(Counter).increment as mock_increment:
            given().call(mock_increment(any(int))).returns(999)

            counter1 = Counter(0)
            counter2 = Counter(100)

            assert counter1.increment(1) == 999
            assert counter2.increment(2) == 999

    def test_patch_instance_method_raises(self):
        with patch(Counter).increment as mock_increment:
            given().call(mock_increment(0)).raises(ValueError("cannot increment by zero"))

            counter = Counter(5)
            with pytest.raises(ValueError) as exc_info:
                counter.increment(0)

            assert "cannot increment by zero" in str(exc_info.value)

    def test_patch_instance_method_runs(self):
        call_log: list[int] = []

        def log_and_return(args: CallArguments) -> int:
            amount = args.get_by_name("amount", int)
            call_log.append(amount)
            return amount * 10

        with patch(Counter).increment as mock_increment:
            given().call(mock_increment(any(int))).runs(log_and_return)

            counter = Counter(0)
            assert counter.increment(3) == 30
            assert counter.increment(5) == 50

        assert call_log == [3, 5]

    def test_patch_instance_method_type_validation(self):
        with patch(Counter).increment as mock_increment:
            with pytest.raises(TMockStubbingError) as exc_info:
                given().call(mock_increment("not an int")).returns(0)

            assert "Invalid type for argument 'amount'" in str(exc_info.value)

    def test_patch_instance_method_return_type_validation(self):
        with patch(Counter).increment as mock_increment:
            with pytest.raises(TMockStubbingError) as exc_info:
                given().call(mock_increment(1)).returns("not an int")

            assert "Invalid return type" in str(exc_info.value)


class TestInstanceMethodPatchingAsync:
    @pytest.mark.asyncio
    async def test_patch_async_instance_method(self):
        with patch(Counter).async_increment as mock_increment:
            given().call(mock_increment(10)).returns(100)

            counter = Counter(5)
            result = await counter.async_increment(10)
            assert result == 100

        # Original restored
        counter = Counter(5)
        result = await counter.async_increment(10)
        assert result == 15

    @pytest.mark.asyncio
    async def test_patch_async_instance_method_with_matcher(self):
        with patch(Counter).async_increment as mock_increment:
            given().call(mock_increment(any(int))).returns(999)

            counter = Counter(0)
            result1 = await counter.async_increment(1)
            result2 = await counter.async_increment(100)

            assert result1 == 999
            assert result2 == 999

    @pytest.mark.asyncio
    async def test_patch_async_instance_method_raises(self):
        with patch(Counter).async_increment as mock_increment:
            given().call(mock_increment(any(int))).raises(ConnectionError("network error"))

            counter = Counter(0)
            with pytest.raises(ConnectionError):
                await counter.async_increment(5)

    @pytest.mark.asyncio
    async def test_patch_async_instance_method_verify(self):
        with patch(Counter).async_increment as mock_increment:
            given().call(mock_increment(any(int))).returns(0)

            counter = Counter(0)
            await counter.async_increment(5)
            await counter.async_increment(10)

            verify().call(mock_increment(5)).once()
            verify().call(mock_increment(10)).once()

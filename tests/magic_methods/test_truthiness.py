import pytest

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError


class SimpleClass:
    pass


class CollectionClass:
    def __len__(self) -> int:
        return 0

    def __contains__(self, item: str) -> bool:
        return False


class LogicalClass:
    def __bool__(self) -> bool:
        return True


class ComplexClass:
    """Defines both len and bool."""

    def __len__(self) -> int:
        return 0

    def __bool__(self) -> bool:
        return False


class TestTruthinessAndContainment:
    # --- Default Behavior ---

    def test_simple_class_truthiness_default(self):
        """Verify that a class without __bool__ or __len__ is always True and doesn't crash."""
        mock = tmock(SimpleClass)

        # This checks standard Python behavior for objects without magic methods
        if mock:
            assert True
        else:
            pytest.fail("Mock should be truthy by default")

        # Verify no unexpected calls were recorded (implicit or otherwise)
        # Since SimpleClass has no methods, nothing should have been intercepted.

    # --- Length (__len__) ---

    def test_len_stubbing(self):
        mock = tmock(CollectionClass)
        given().call(mock.__len__()).returns(5)

        assert len(mock) == 5
        # In boolean context, len > 0 implies True
        assert bool(mock) is True

        verify().call(mock.__len__()).times(2)

    def test_len_zero_implies_false(self):
        mock = tmock(CollectionClass)
        given().call(mock.__len__()).returns(0)

        assert len(mock) == 0
        assert bool(mock) is False

        verify().call(mock.__len__()).times(2)

    def test_len_return_type_validation(self):
        mock = tmock(CollectionClass)

        # Must return int
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock.__len__()).returns("five")
        assert "Invalid return type" in str(exc.value)

    # --- Containment (__contains__) ---

    def test_contains_stubbing(self):
        mock = tmock(CollectionClass)
        given().call(mock.__contains__("valid")).returns(True)
        given().call(mock.__contains__("invalid")).returns(False)

        assert "valid" in mock
        assert "invalid" not in mock

        verify().call(mock.__contains__("valid")).once()
        verify().call(mock.__contains__("invalid")).once()

    def test_contains_with_matchers(self):
        mock = tmock(CollectionClass)
        given().call(mock.__contains__(any(str))).returns(True)

        assert "anything" in mock
        assert "another" in mock

        verify().call(mock.__contains__(any(str))).times(2)

    def test_contains_return_type_validation(self):
        mock = tmock(CollectionClass)
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock.__contains__("x")).returns(123)  # Not bool
        assert "Invalid return type" in str(exc.value)

    # --- Boolean (__bool__) ---

    def test_bool_stubbing(self):
        mock = tmock(LogicalClass)

        given().call(mock.__bool__()).returns(False)
        assert not mock

        given().call(mock.__bool__()).returns(True)
        assert mock

        verify().call(mock.__bool__()).times(2)

    def test_bool_return_type_validation(self):
        mock = tmock(LogicalClass)
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock.__bool__()).returns(None)
        assert "Invalid return type" in str(exc.value)

    # --- Precedence & Interactions ---

    def test_bool_precedence_over_len(self):
        """Python prefers __bool__ over __len__ if both exist."""
        mock = tmock(ComplexClass)

        # Even if len is 10 (would imply True), bool returning False wins
        # Note: We only need to stub what Python calls.
        given().call(mock.__bool__()).returns(False)

        if mock:
            pytest.fail("Should be false due to __bool__")

        verify().call(mock.__bool__()).once()
        # Ensure __len__ was NOT called
        verify().call(mock.__len__()).never()

    # --- Strictness ---

    def test_strictness_raises_if_unstubbed(self):
        """Verify strict mode raises error if methods exist but aren't stubbed."""
        mock = tmock(CollectionClass)

        with pytest.raises(TMockUnexpectedCallError):
            len(mock)

        with pytest.raises(TMockUnexpectedCallError):
            if mock:  # triggers __len__
                pass


class ValidatorService:
    def __init__(self, blocked_items: CollectionClass):
        self.blocked_items = blocked_items

    def is_valid(self, item: str) -> bool:
        if not self.blocked_items:
            # If blocklist is empty, everything is valid
            return True
        return item not in self.blocked_items


class TestTruthinessIntegration:
    def test_validator_service_empty_blocklist(self):
        mock_list = tmock(CollectionClass)
        service = ValidatorService(mock_list)

        # Simulate empty list check
        given().call(mock_list.__len__()).returns(0)

        assert service.is_valid("bad_item") is True

        verify().call(mock_list.__len__()).once()
        verify().call(mock_list.__contains__(any())).never()

    def test_validator_service_checks_containment(self):
        mock_list = tmock(CollectionClass)
        service = ValidatorService(mock_list)

        # Simulate non-empty list
        given().call(mock_list.__len__()).returns(5)
        given().call(mock_list.__contains__("bad_item")).returns(True)

        assert service.is_valid("bad_item") is False

        verify().call(mock_list.__len__()).once()
        verify().call(mock_list.__contains__("bad_item")).once()

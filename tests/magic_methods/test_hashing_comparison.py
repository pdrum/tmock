import pytest

from tmock import given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError


class ComparablePoint:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ComparablePoint):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __lt__(self, other: "ComparablePoint") -> bool:
        return (self.x, self.y) < (other.x, other.y)


class SimplePoint:
    """No comparison or hash defined."""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class TestComparison:
    def test_eq_stubbing(self):
        mock1 = tmock(ComparablePoint)
        mock2 = tmock(ComparablePoint)

        # Stub equality
        given().call(mock1.__eq__(mock2)).returns(True)

        assert mock1 == mock2
        verify().call(mock1.__eq__(mock2)).once()

    def test_ne_stubbing(self):
        # Python 3 automatically derives __ne__ from __eq__ if not defined,
        # but if it IS defined in the class, tmock will intercept it.
        # ComparablePoint doesn't define __ne__, so it shouldn't be intercepted.
        mock1 = tmock(ComparablePoint)
        mock2 = tmock(ComparablePoint)

        given().call(mock1.__eq__(mock2)).returns(False)
        assert mock1 != mock2

    def test_lt_stubbing(self):
        mock1 = tmock(ComparablePoint)
        mock2 = tmock(ComparablePoint)

        given().call(mock1.__lt__(mock2)).returns(True)
        assert mock1 < mock2
        verify().call(mock1.__lt__(mock2)).once()

    def test_strictness_raises_if_not_stubbed(self):
        mock1 = tmock(ComparablePoint)
        mock2 = tmock(ComparablePoint)

        with pytest.raises(TMockUnexpectedCallError):
            _ = mock1 == mock2

    def test_default_identity_fallback(self):
        """Verify that classes without __eq__ use default identity (no crash)."""
        mock1 = tmock(SimplePoint)
        mock2 = tmock(SimplePoint)

        # These shouldn't crash because __eq__ isn't intercepted
        assert mock1 == mock1
        assert mock1 != mock2

        # Verify it uses identity
        assert not (mock1 == mock2)

        # We can verify it's NOT intercepted by checking the mock's internal state
        # or just by the fact that it didn't raise TMockUnexpectedCallError.
        # Let's check that it's not in the interceptors.
        interceptors = object.__getattribute__(mock1, "__method_interceptors")
        assert "__eq__" not in interceptors


class TestHashing:
    def test_hash_stubbing(self):
        mock = tmock(ComparablePoint)
        given().call(mock.__hash__()).returns(12345)

        assert hash(mock) == 12345
        verify().call(mock.__hash__()).once()

    def test_hash_must_return_int(self):
        mock = tmock(ComparablePoint)
        with pytest.raises(TMockStubbingError):
            given().call(mock.__hash__()).returns("not an int")

    def test_strictness_raises_if_not_stubbed(self):
        mock = tmock(ComparablePoint)
        with pytest.raises(TMockUnexpectedCallError):
            hash(mock)


class TestHashingComparisonIntegration:
    def test_in_dictionary(self):
        mock = tmock(ComparablePoint)

        # When used as dict key, Python calls hash() then eq() on collision
        given().call(mock.__hash__()).returns(100)

        d = {mock: "value"}
        assert d[mock] == "value"

        verify().call(mock.__hash__()).at_least(1)

    def test_in_set(self):
        mock1 = tmock(ComparablePoint)
        mock2 = tmock(ComparablePoint)

        given().call(mock1.__hash__()).returns(1)
        given().call(mock2.__hash__()).returns(2)

        s = {mock1, mock2}
        assert len(s) == 2
        assert mock1 in s
        assert mock2 in s

    def test_set_collision_calls_eq(self):
        mock1 = tmock(ComparablePoint)
        mock2 = tmock(ComparablePoint)

        # Force hash collision
        given().call(mock1.__hash__()).returns(42)
        given().call(mock2.__hash__()).returns(42)

        # When hashes collide, Python calls __eq__ to check if they are the same object
        given().call(mock1.__eq__(mock2)).returns(False)

        s = {mock1, mock2}
        assert len(s) == 2

        verify().call(mock1.__hash__()).once()
        verify().call(mock2.__hash__()).once()
        verify().call(mock1.__eq__(mock2)).once()

import pytest

from tmock import any, given, reset, reset_behaviors, reset_interactions, tmock, verify
from tmock.exceptions import TMockUnexpectedCallError


class SampleClass:
    def greet(self, name: str) -> str:
        return ""

    def add(self, a: int, b: int) -> int:
        return 0


class PersonClass:
    name: str
    age: int


class TestReset:
    def test_reset_clears_interactions_and_behaviors(self):
        mock = tmock(SampleClass)
        given().call(mock.greet(any(str))).returns("Hello")
        mock.greet("Alice")
        mock.greet("Bob")

        reset(mock)

        # Interactions cleared - verify sees nothing
        verify().call(mock.greet(any(str))).never()

        # Behaviors cleared - should raise
        with pytest.raises(TMockUnexpectedCallError):
            mock.greet("Charlie")

    def test_reset_works_on_multiple_methods(self):
        mock = tmock(SampleClass)
        given().call(mock.greet(any(str))).returns("Hi")
        given().call(mock.add(any(int), any(int))).returns(42)
        mock.greet("Alice")
        mock.add(1, 2)

        reset(mock)

        verify().call(mock.greet(any(str))).never()
        verify().call(mock.add(any(int), any(int))).never()
        with pytest.raises(TMockUnexpectedCallError):
            mock.greet("Bob")
        with pytest.raises(TMockUnexpectedCallError):
            mock.add(3, 4)


class TestResetInteractions:
    def test_reset_interactions_clears_call_history(self):
        mock = tmock(SampleClass)
        given().call(mock.greet(any(str))).returns("Hello")
        mock.greet("Alice")
        mock.greet("Bob")

        reset_interactions(mock)

        # Behaviors preserved - should still work
        assert mock.greet("Charlie") == "Hello"

        # Interactions cleared - previous calls gone, only Charlie counted
        verify().call(mock.greet("Alice")).never()
        verify().call(mock.greet("Bob")).never()
        verify().call(mock.greet("Charlie")).once()

    def test_reset_interactions_preserves_behaviors(self):
        mock = tmock(SampleClass)
        given().call(mock.greet("Alice")).returns("Hi Alice")
        given().call(mock.greet("Bob")).returns("Hi Bob")

        reset_interactions(mock)

        # Both stubs still work
        assert mock.greet("Alice") == "Hi Alice"
        assert mock.greet("Bob") == "Hi Bob"


class TestResetBehaviors:
    def test_reset_behaviors_clears_stubs(self):
        mock = tmock(SampleClass)
        given().call(mock.greet(any(str))).returns("Hello")
        mock.greet("Alice")

        reset_behaviors(mock)

        # Behaviors cleared - should raise
        with pytest.raises(TMockUnexpectedCallError):
            mock.greet("Bob")

    def test_reset_behaviors_preserves_interactions(self):
        mock = tmock(SampleClass)
        given().call(mock.greet(any(str))).returns("Hello")
        mock.greet("Alice")
        mock.greet("Bob")

        reset_behaviors(mock)

        # Interactions preserved
        verify().call(mock.greet("Alice")).once()
        verify().call(mock.greet("Bob")).once()
        verify().call(mock.greet(any(str))).times(2)


class TestResetWithFields:
    def test_reset_clears_field_getters(self):
        mock = tmock(PersonClass)
        given().get(mock.name).returns("Alice")
        _ = mock.name

        reset(mock)

        verify().get(mock.name).never()
        with pytest.raises(TMockUnexpectedCallError):
            _ = mock.name

    def test_reset_clears_field_setters(self):
        mock = tmock(PersonClass)
        given().set(mock.name, any(str)).returns(None)
        mock.name = "Alice"

        reset(mock)

        verify().set(mock.name, any(str)).never()
        with pytest.raises(TMockUnexpectedCallError):
            mock.name = "Bob"

    def test_reset_interactions_on_fields(self):
        mock = tmock(PersonClass)
        given().get(mock.name).returns("Alice")
        given().set(mock.name, any(str)).returns(None)
        _ = mock.name
        mock.name = "Bob"

        reset_interactions(mock)

        # Behaviors preserved
        assert mock.name == "Alice"
        mock.name = "Charlie"

        # Only new interactions counted
        verify().get(mock.name).once()
        verify().set(mock.name, "Charlie").once()

    def test_reset_behaviors_on_fields(self):
        mock = tmock(PersonClass)
        given().get(mock.name).returns("Alice")
        given().set(mock.name, any(str)).returns(None)
        _ = mock.name
        mock.name = "Bob"

        reset_behaviors(mock)

        # Interactions preserved
        verify().get(mock.name).once()
        verify().set(mock.name, "Bob").once()

        # Behaviors cleared
        with pytest.raises(TMockUnexpectedCallError):
            _ = mock.name


class TestResetMultipleTimes:
    def test_can_reset_multiple_times(self):
        mock = tmock(SampleClass)

        # First round
        given().call(mock.greet(any(str))).returns("Round 1")
        assert mock.greet("Alice") == "Round 1"
        verify().call(mock.greet(any(str))).once()

        reset(mock)

        # Second round
        given().call(mock.greet(any(str))).returns("Round 2")
        assert mock.greet("Bob") == "Round 2"
        verify().call(mock.greet("Alice")).never()
        verify().call(mock.greet("Bob")).once()

        reset(mock)

        # Third round - fresh state
        verify().call(mock.greet(any(str))).never()
        with pytest.raises(TMockUnexpectedCallError):
            mock.greet("Charlie")

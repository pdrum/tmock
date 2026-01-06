import pytest

from tmock import any, given, tmock, verify
from tmock.exceptions import TMockStubbingError, TMockUnexpectedCallError


class CustomDict:
    def __getitem__(self, key: str) -> int:
        return 0

    def __setitem__(self, key: str, value: int) -> None:
        pass

    def __delitem__(self, key: str) -> None:
        pass


class ReadOnlyContainer:
    def __getitem__(self, index: int) -> str:
        return "val"


class TestContainerGetItem:
    def test_getitem_stubbing_and_return(self):
        mock = tmock(CustomDict)
        given().call(mock["a"]).returns(10)
        given().call(mock["b"]).returns(20)

        assert mock["a"] == 10
        assert mock["b"] == 20

        verify().call(mock["a"]).once()
        verify().call(mock["b"]).once()

    def test_getitem_matchers(self):
        mock = tmock(CustomDict)
        given().call(mock[any(str)]).returns(99)

        assert mock["x"] == 99
        assert mock["y"] == 99

        verify().call(mock["x"]).once()

    def test_getitem_type_validation(self):
        mock = tmock(CustomDict)

        # Key must be str
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock[123]).returns(1)

        assert "Invalid type for argument 'key'" in str(exc.value)

    def test_getitem_return_type_validation(self):
        mock = tmock(CustomDict)

        # Return must be int
        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock["key"]).returns("not int")

        assert "Invalid return type" in str(exc.value)

    def test_getitem_raises_exception(self):
        mock = tmock(CustomDict)
        given().call(mock["missing"]).raises(KeyError("missing"))

        with pytest.raises(KeyError, match="missing"):
            _ = mock["missing"]


class TestContainerSetItem:
    def test_setitem_stubbing(self):
        mock = tmock(CustomDict)
        # __setitem__ returns None usually
        given().call(mock.__setitem__("key", 100)).returns(None)

        mock["key"] = 100

        verify().call(mock.__setitem__("key", 100)).once()

    def test_setitem_matchers(self):
        mock = tmock(CustomDict)
        given().call(mock.__setitem__(any(str), any(int))).returns(None)

        mock["a"] = 1
        mock["b"] = 2

        verify().call(mock.__setitem__("a", 1)).once()
        verify().call(mock.__setitem__("b", 2)).once()

    def test_setitem_key_type_validation(self):
        mock = tmock(CustomDict)

        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock.__setitem__(123, 10)).returns(None)
        assert "Invalid type for argument 'key'" in str(exc.value)

    def test_setitem_value_type_validation(self):
        mock = tmock(CustomDict)

        with pytest.raises(TMockStubbingError) as exc:
            given().call(mock.__setitem__("key", "not int")).returns(None)
        assert "Invalid type for argument 'value'" in str(exc.value)


class TestContainerDelItem:
    def test_delitem_stubbing(self):
        mock = tmock(CustomDict)
        given().call(mock.__delitem__("key")).returns(None)

        del mock["key"]

        verify().call(mock.__delitem__("key")).once()

    def test_delitem_validation(self):
        mock = tmock(CustomDict)

        with pytest.raises(TMockStubbingError):
            given().call(mock.__delitem__(123)).returns(None)


class TestContainerStrictness:
    def test_raises_if_not_stubbed(self):
        mock = tmock(CustomDict)

        with pytest.raises(TMockUnexpectedCallError):
            _ = mock["unexpected"]

    def test_raises_if_method_missing(self):
        """Test that methods are not added if they don't exist in original class."""
        mock = tmock(ReadOnlyContainer)

        # __setitem__ is not defined on ReadOnlyContainer
        with pytest.raises(TypeError) as exc_info:
            # Python itself raises TypeError: 'TMock' object does not support item assignment
            mock[0] = "val"
            assert "'TMock' object does not support item assignment" in str(exc_info.value)

        # TMock shouldn't have even generated the interceptor
        assert not hasattr(mock, "__setitem__")
        assert not hasattr(mock, "__delitem__")
        assert hasattr(mock, "__getitem__")

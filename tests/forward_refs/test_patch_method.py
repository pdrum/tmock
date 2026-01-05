"""Tests for forward references in tpatch.method()."""

import pytest

from tests.forward_refs.fixtures import Container, Item, Node
from tmock import given, tpatch
from tmock.exceptions import TMockStubbingError


class TestForwardRefReturnType:
    def test_accepts_valid(self) -> None:
        with tpatch.method(Node, "get_parent") as mock:
            node = Node()
            given().call(mock()).returns(node)

            instance = Node()
            assert instance.get_parent() is node

    def test_rejects_invalid(self) -> None:
        with tpatch.method(Node, "get_parent") as mock:
            with pytest.raises(TMockStubbingError, match="Invalid return type"):
                given().call(mock()).returns("not a node")


class TestForwardRefParameter:
    def test_accepts_valid(self) -> None:
        with tpatch.method(Container, "add_item") as mock:
            item = Item("test")
            given().call(mock(item)).returns(True)

            container = Container()
            assert container.add_item(item) is True

    def test_rejects_invalid(self) -> None:
        with tpatch.method(Container, "add_item") as mock:
            with pytest.raises(TMockStubbingError, match="Invalid type for argument"):
                given().call(mock("not an item"))

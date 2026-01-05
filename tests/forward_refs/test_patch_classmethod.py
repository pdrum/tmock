"""Tests for forward references in tpatch.class_method()."""

import pytest

from tests.forward_refs.fixtures import Node
from tmock import given, tpatch
from tmock.exceptions import TMockStubbingError


class TestForwardRefReturnType:
    def test_accepts_valid(self) -> None:
        with tpatch.class_method(Node, "create") as mock:
            node = Node()
            given().call(mock()).returns(node)

            assert Node.create() is node

    def test_rejects_invalid(self) -> None:
        with tpatch.class_method(Node, "create") as mock:
            with pytest.raises(TMockStubbingError, match="Invalid return type"):
                given().call(mock()).returns("not a node")

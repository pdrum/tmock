"""Tests for forward references in tpatch.function()."""

import pytest

from tests.forward_refs import fixtures
from tests.forward_refs.fixtures import Node
from tmock import given, tpatch
from tmock.exceptions import TMockStubbingError


class TestForwardRefReturnType:
    def test_accepts_valid(self) -> None:
        with tpatch.function("tests.forward_refs.fixtures.create_node") as mock:
            node = Node()
            given().call(mock()).returns(node)

            result = fixtures.create_node()
            assert result is node

    def test_rejects_invalid(self) -> None:
        with tpatch.function("tests.forward_refs.fixtures.create_node") as mock:
            with pytest.raises(TMockStubbingError, match="Invalid return type"):
                given().call(mock()).returns("not a node")


class TestForwardRefParameter:
    def test_accepts_valid(self) -> None:
        with tpatch.function("tests.forward_refs.fixtures.process_node") as mock:
            node = Node()
            given().call(mock(node)).returns("processed")

            result = fixtures.process_node(node)
            assert result == "processed"

    def test_rejects_invalid(self) -> None:
        with tpatch.function("tests.forward_refs.fixtures.process_node") as mock:
            with pytest.raises(TMockStubbingError, match="Invalid type for argument"):
                given().call(mock("not a node"))

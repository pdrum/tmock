"""Tests for forward reference resolution in tmock()."""

import pytest

from tests.forward_refs.fixtures import (
    AsyncService,
    Container,
    Item,
    LinkedList,
    ListNode,
    Node,
    Result,
)
from tmock import given, tmock, verify
from tmock.exceptions import TMockStubbingError


class TestSelfReferencingReturnType:
    def test_accepts_valid(self) -> None:
        mock = tmock(Node)
        node = Node()

        given().call(mock.get_parent()).returns(node)

        assert mock.get_parent() is node

    def test_rejects_invalid(self) -> None:
        mock = tmock(Node)

        with pytest.raises(TMockStubbingError, match="Invalid return type"):
            given().call(mock.get_parent()).returns("not a node")  # type: ignore[arg-type]


class TestForwardRefParameter:
    def test_accepts_valid(self) -> None:
        mock = tmock(Container)
        item = Item("test")

        given().call(mock.add_item(item)).returns(True)

        assert mock.add_item(item) is True

    def test_rejects_invalid(self) -> None:
        mock = tmock(Container)

        with pytest.raises(TMockStubbingError, match="Invalid type for argument"):
            given().call(mock.add_item("not an item"))  # type: ignore[arg-type]


class TestCrossClassForwardRef:
    def test_accepts_valid(self) -> None:
        mock = tmock(LinkedList)
        node = ListNode(42)

        given().call(mock.head()).returns(node)

        assert mock.head() is node

    def test_rejects_invalid(self) -> None:
        mock = tmock(LinkedList)

        with pytest.raises(TMockStubbingError, match="Invalid return type"):
            given().call(mock.head()).returns("not a ListNode")  # type: ignore[arg-type]

    def test_chained_forward_refs(self) -> None:
        mock = tmock(ListNode)
        next_node = ListNode(2)

        given().call(mock.next_node()).returns(next_node)

        assert mock.next_node() is next_node


class TestAsyncMethodsWithForwardRefs:
    @pytest.mark.asyncio
    async def test_self_ref_accepts_valid(self) -> None:
        mock = tmock(AsyncService)
        service = AsyncService()

        given().call(mock.fetch()).returns(service)

        result = await mock.fetch()
        assert result is service

    @pytest.mark.asyncio
    async def test_self_ref_rejects_invalid(self) -> None:
        mock = tmock(AsyncService)

        with pytest.raises(TMockStubbingError, match="Invalid return type"):
            given().call(mock.fetch()).returns("not a service")  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_cross_class_ref_accepts_valid(self) -> None:
        mock = tmock(AsyncService)
        result = Result()

        given().call(mock.get_result()).returns(result)

        assert await mock.get_result() is result


class TestVerificationWithForwardRefs:
    def test_verification_works(self) -> None:
        mock = tmock(Node)
        node = Node()

        given().call(mock.get_parent()).returns(node)

        mock.get_parent()

        verify().call(mock.get_parent()).once()

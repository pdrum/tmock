"""Test fixtures with forward reference type annotations."""


class Node:
    """A class with forward reference to itself."""

    def get_parent(self) -> "Node":
        return Node()

    def get_child(self, name: str) -> "Node":
        return Node()

    @classmethod
    def create(cls) -> "Node":
        return cls()

    @staticmethod
    def root() -> "Node":
        return Node()


class LinkedList:
    """A class with forward references to another class."""

    def head(self) -> "ListNode":
        return ListNode(0)


class ListNode:
    """Node for LinkedList."""

    def __init__(self, value: int):
        self.value = value

    def next_node(self) -> "ListNode":
        return ListNode(self.value + 1)


class Container:
    """Class with forward ref parameters."""

    def add_item(self, item: "Item") -> bool:
        return True

    def get_item(self, key: str) -> "Item":
        return Item(key)


class Item:
    """Item class for Container."""

    def __init__(self, key: str):
        self.key = key


class AsyncService:
    """Class with async methods using forward refs."""

    async def fetch(self) -> "AsyncService":
        return self

    async def get_result(self) -> "Result":
        return Result()


class Result:
    """Result class for AsyncService."""

    pass


def create_node() -> "Node":
    """Function with forward reference return type."""
    return Node()


def process_node(node: "Node") -> str:
    """Function with forward reference parameter."""
    return "real"


def unresolvable_ref() -> "NonExistent":  # type: ignore[name-defined]  # noqa: F821
    """Function with unresolvable forward reference."""
    pass

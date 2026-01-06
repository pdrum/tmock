from tmock import any, given, tpatch, verify


class ComparableItem:
    def __init__(self, val: int):
        self.val = val

    def __eq__(self, other: object) -> bool:
        return False

    def __lt__(self, other: "ComparableItem") -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __bool__(self) -> bool:
        return True


class TestPatchingComparisonMagic:
    def test_eq_patching(self):
        with tpatch.method(ComparableItem, "__eq__") as mock:
            # We are patching __eq__ on the class, so it affects all instances
            given().call(mock(any())).returns(True)

            a = ComparableItem(1)
            b = ComparableItem(2)

            assert a == b
            verify().call(mock(any())).once()

    def test_lt_patching(self):
        with tpatch.method(ComparableItem, "__lt__") as mock:
            given().call(mock(any())).returns(True)

            a = ComparableItem(10)
            b = ComparableItem(5)

            assert a < b
            verify().call(mock(any())).once()

    def test_hash_patching(self):
        with tpatch.method(ComparableItem, "__hash__") as mock:
            given().call(mock()).returns(12345)

            a = ComparableItem(1)
            assert hash(a) == 12345

            verify().call(mock()).once()

    def test_bool_patching(self):
        with tpatch.method(ComparableItem, "__bool__") as mock:
            given().call(mock()).returns(False)

            a = ComparableItem(1)
            assert not a

            verify().call(mock()).once()

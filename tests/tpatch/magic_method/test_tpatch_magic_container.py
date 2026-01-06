import pytest

from tmock import given, tpatch, verify


class ConfigMap:
    def __getitem__(self, key: str) -> int:
        return 0

    def __setitem__(self, key: str, value: int) -> None:
        pass

    def __delitem__(self, key: str) -> None:
        pass

    def __len__(self) -> int:
        return 0

    def __contains__(self, key: str) -> bool:
        return False


class TestPatchingContainerMagic:
    def test_getitem_patching(self):
        with tpatch.method(ConfigMap, "__getitem__") as mock:
            given().call(mock("key")).returns(42)

            c = ConfigMap()
            assert c["key"] == 42

            verify().call(mock("key")).once()

    def test_setitem_patching(self):
        with tpatch.method(ConfigMap, "__setitem__") as mock:
            given().call(mock("key", 100)).returns(None)

            c = ConfigMap()
            c["key"] = 100

            verify().call(mock("key", 100)).once()

    def test_delitem_patching(self):
        with tpatch.method(ConfigMap, "__delitem__") as mock:
            given().call(mock("key")).returns(None)

            c = ConfigMap()
            del c["key"]

            verify().call(mock("key")).once()

    def test_len_patching(self):
        with tpatch.method(ConfigMap, "__len__") as mock:
            given().call(mock()).returns(10)

            c = ConfigMap()
            assert len(c) == 10

            verify().call(mock()).once()

    def test_contains_patching(self):
        with tpatch.method(ConfigMap, "__contains__") as mock:
            given().call(mock("found")).returns(True)
            given().call(mock("missing")).returns(False)

            c = ConfigMap()
            assert "found" in c
            assert "missing" not in c

            verify().call(mock("found")).once()

    def test_validation_container(self):
        with tpatch.method(ConfigMap, "__getitem__") as mock:
            # ConfigMap.__getitem__ expects str key
            with pytest.raises(Exception):  # TMockStubbingError
                given().call(mock(123))

        with tpatch.method(ConfigMap, "__len__") as mock:
            # Must return int
            with pytest.raises(Exception):
                given().call(mock()).returns("string")

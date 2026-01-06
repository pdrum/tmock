from tmock import given, tpatch, verify


class User:
    def __str__(self) -> str:
        return "RealUser"

    def __repr__(self) -> str:
        return "<RealUser>"


class TestPatchingStringMagic:
    def test_str_patching(self):
        with tpatch.method(User, "__str__") as mock:
            given().call(mock()).returns("MockedUser")

            u = User()
            assert str(u) == "MockedUser"

            verify().call(mock()).once()

    def test_repr_patching(self):
        with tpatch.method(User, "__repr__") as mock:
            given().call(mock()).returns("<Mocked>")

            u = User()
            assert repr(u) == "<Mocked>"

            verify().call(mock()).once()

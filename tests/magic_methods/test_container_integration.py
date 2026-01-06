from tmock import given, tmock, verify


class CustomDict:
    def __getitem__(self, key: str) -> int:
        return 0

    def __setitem__(self, key: str, value: int) -> None:
        pass

    def __delitem__(self, key: str) -> None:
        pass


class ConfigService:
    def __init__(self, config: CustomDict):
        self.config = config

    def update_timeout(self, new_val: int):
        self.config["timeout"] = new_val

    def get_timeout(self) -> int:
        return self.config["timeout"]


class TestContainerIntegration:
    def test_config_service(self):
        config_mock = tmock(CustomDict)
        service = ConfigService(config_mock)

        # Stub getter
        given().call(config_mock["timeout"]).returns(500)
        # Stub setter
        given().call(config_mock.__setitem__("timeout", 1000)).returns(None)

        assert service.get_timeout() == 500
        service.update_timeout(1000)

        verify().call(config_mock["timeout"]).once()
        verify().call(config_mock.__setitem__("timeout", 1000)).once()

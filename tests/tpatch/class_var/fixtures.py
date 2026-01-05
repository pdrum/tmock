"""Fixtures for tpatch.class_var tests."""

from typing import ClassVar


class Settings:
    """Class with class variables."""

    DEBUG: ClassVar[bool] = False
    MAX_RETRIES: ClassVar[int] = 3
    API_URL: ClassVar[str] = "https://api.example.com"

    UNTYPED_VAR = "default"


class ConfigWithClassVars:
    """Another class with class variables."""

    TIMEOUT: ClassVar[int] = 30
    ENABLED: ClassVar[bool] = True

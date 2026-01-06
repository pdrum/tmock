class TMockError(Exception):
    """Base class for all tmock exceptions."""

    pass


class TMockStubbingError(TMockError):
    pass


class TMockVerificationError(TMockError, AssertionError):
    pass


class TMockUnexpectedCallError(TMockError):
    pass


class TMockPatchingError(TMockError):
    pass


class TMockResetError(TMockError):
    pass

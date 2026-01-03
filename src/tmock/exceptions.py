class TMockStubbingError(Exception):
    pass


class TMockVerificationError(AssertionError):
    pass


class TMockUnexpectedCallError(Exception):
    pass


class TMockPatchingError(Exception):
    pass

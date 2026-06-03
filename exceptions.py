# custom exceptions for the app


class FlashcardsError(Exception):
    """base error for app"""

    pass


class ApiError(FlashcardsError):
    """raised when something goes wrong with the ai api"""

    pass


class FileNotSupportedError(FlashcardsError):
    """raised when user tries to open a file we cant read"""

    pass


class StorageError(FlashcardsError):
    """raised when saving or loading fails"""

    pass

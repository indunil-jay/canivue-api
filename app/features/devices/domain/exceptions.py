from app.core.exceptions import ConflictException


class CollarNotConnectedError(ConflictException):
    def __init__(self, action: str) -> None:
        super().__init__(message=f"The collar must be connected to {action}.")


class CollarNotPairedError(ConflictException):
    def __init__(self) -> None:
        super().__init__(message="No collar is paired with this Dog.")

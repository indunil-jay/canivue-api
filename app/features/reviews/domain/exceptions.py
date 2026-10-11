from app.core.exceptions import ConflictException


class AppointmentNotCompletedError(ConflictException):
    def __init__(self) -> None:
        super().__init__(message="Only a completed appointment can be reviewed.")


class AlreadyReviewedError(ConflictException):
    def __init__(self) -> None:
        super().__init__(message="This appointment has already been reviewed.")

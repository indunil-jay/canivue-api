from app.core.exceptions import ConflictException, NotFoundException, ValidationException


class AppointmentNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Appointment not found.")


class BookingRejectedError(ValidationException):
    pass


class SlotTakenError(ConflictException):
    def __init__(self) -> None:
        super().__init__(message="The veterinarian already has an appointment at that time.")


class InvalidAppointmentTransitionError(ConflictException):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(message=f"An appointment that is '{current}' cannot become '{target}'.")

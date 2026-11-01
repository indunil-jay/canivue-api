from app.core.exceptions import NotFoundException, ValidationException


class VeterinarianNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Veterinarian not found.")


class UnknownWeekdayError(ValidationException):
    def __init__(self, day: str) -> None:
        super().__init__(message=f"'{day}' is not a day of the week.")

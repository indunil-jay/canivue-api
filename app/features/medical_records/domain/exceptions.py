from app.core.exceptions import ForbiddenException, NotFoundException


class MedicalRecordNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Medical record not found.")


class ClinicalRecordForbiddenError(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(
            message="Only a treating veterinarian can add a diagnosis, prescription or lab result."
        )


class NotRecordAuthorError(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(message="Only the author can delete a medical record.")

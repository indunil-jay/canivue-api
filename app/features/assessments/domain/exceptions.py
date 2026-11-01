from app.core.exceptions import NotFoundException, ValidationException


class PredictionNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Prediction not found.")


class NoEvidenceError(ValidationException):
    def __init__(self) -> None:
        super().__init__(
            message="An Assessment needs a photo, a symptom description or recent collar data."
        )

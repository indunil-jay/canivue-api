from app.core.exceptions import NotFoundException


class CareTaskNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Care task not found.")

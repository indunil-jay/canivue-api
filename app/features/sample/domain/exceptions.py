from app.core.exceptions import NotFoundException, ConflictException


class SampleNotFoundException(NotFoundException):
    """Raised when a sample item is not found."""

    def __init__(self, sample_id: str):
        super().__init__(
            message=f"Sample with ID '{sample_id}' was not found.",
            details={"sample_id": sample_id},
        )


class SampleTitleAlreadyExistsException(ConflictException):
    """Raised when attempting to create a sample with an existing title."""

    def __init__(self, title: str):
        super().__init__(
            message=f"Sample with title '{title}' already exists.",
            details={"title": title},
        )

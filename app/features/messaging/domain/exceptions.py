from app.core.exceptions import ForbiddenException, NotFoundException


class ConversationNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Conversation not found.")


class SummaryNotAllowedError(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(message="Only the veterinarian can post a consultation summary.")

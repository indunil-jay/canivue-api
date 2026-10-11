from app.core.exceptions import NotFoundException


class NotificationNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Notification not found.")

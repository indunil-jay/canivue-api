from app.core.exceptions import NotFoundException


class CommunityNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Community not found.")


class PostNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Post not found.")

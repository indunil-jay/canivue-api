from dataclasses import dataclass
from typing import Protocol

from app.core.exceptions import AppException, NotFoundException

IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
DOCUMENT_TYPES = IMAGE_TYPES | {"application/pdf"}

_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),
    "application/pdf": (b"%PDF-",),
}


class FileTooLargeError(AppException):
    def __init__(self, max_bytes: int):
        super().__init__(
            message=f"File is larger than the {max_bytes // (1024 * 1024)} MB limit.",
            status_code=413,
        )


class UnsupportedFileTypeError(AppException):
    def __init__(self, allowed: frozenset[str]):
        super().__init__(
            message=f"Unsupported file type. Allowed: {', '.join(sorted(allowed))}.",
            status_code=415,
        )


class StoredFileNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="File not found.")


@dataclass(frozen=True)
class FileContent:
    content: bytes
    content_type: str


class FileStorageProtocol(Protocol):
    async def save(self, content: bytes, content_type: str) -> str:
        """Stores the bytes and returns an opaque file id."""
        ...

    async def load(self, file_id: str) -> FileContent: ...

    async def delete(self, file_id: str) -> None: ...


def validate_upload(
    content: bytes, content_type: str | None, allowed: frozenset[str], max_bytes: int
) -> str:
    """Returns the accepted content type, or raises. The declared type must match the bytes."""
    if len(content) > max_bytes:
        raise FileTooLargeError(max_bytes)
    declared = (content_type or "").split(";")[0].strip().lower()
    if declared not in allowed or not content.startswith(_SIGNATURES[declared]):
        raise UnsupportedFileTypeError(allowed)
    if declared == "image/webp" and content[8:12] != b"WEBP":
        raise UnsupportedFileTypeError(allowed)
    return declared

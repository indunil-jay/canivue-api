import asyncio
import re
import uuid
from pathlib import Path

from fastapi import UploadFile
from fastapi.responses import Response

from app.config import settings
from app.shared.files import (
    FileContent,
    FileStorageProtocol,
    FileTooLargeError,
    StoredFileNotFoundError,
)

_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "application/pdf": "pdf",
}
_CONTENT_TYPES = {ext: content_type for content_type, ext in _EXTENSIONS.items()}
_FILE_ID = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp|pdf)$")


class LocalDiskFileStorage(FileStorageProtocol):
    def __init__(self, root: str):
        self._root = Path(root)

    def _path(self, file_id: str) -> Path:
        # File ids are generated here; anything else (e.g. a path) is refused outright.
        if not _FILE_ID.match(file_id):
            raise StoredFileNotFoundError()
        return self._root / file_id

    async def save(self, content: bytes, content_type: str) -> str:
        file_id = f"{uuid.uuid4().hex}.{_EXTENSIONS[content_type]}"
        self._root.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread((self._root / file_id).write_bytes, content)
        return file_id

    async def load(self, file_id: str) -> FileContent:
        path = self._path(file_id)
        if not path.is_file():
            raise StoredFileNotFoundError()
        content = await asyncio.to_thread(path.read_bytes)
        return FileContent(content=content, content_type=_CONTENT_TYPES[path.suffix[1:]])

    async def delete(self, file_id: str) -> None:
        self._path(file_id).unlink(missing_ok=True)


def get_file_storage() -> FileStorageProtocol:
    return LocalDiskFileStorage(settings.UPLOAD_DIR)


async def read_upload(file: UploadFile) -> bytes:
    """Reads at most one byte past the limit, so an oversized upload is never held in memory."""
    content = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise FileTooLargeError(settings.MAX_UPLOAD_BYTES)
    return content


def file_response(file: FileContent) -> Response:
    return Response(
        content=file.content,
        media_type=file.content_type,
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, max-age=300"},
    )

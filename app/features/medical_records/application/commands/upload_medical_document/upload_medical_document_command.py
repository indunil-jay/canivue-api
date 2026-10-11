from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class UploadMedicalDocumentCommand:
    actor: Actor
    dog_id: str
    title: str
    content: bytes
    content_type: str | None
    max_bytes: int

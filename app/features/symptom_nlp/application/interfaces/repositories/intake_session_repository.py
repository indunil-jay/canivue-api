from typing import Protocol

from app.features.symptom_nlp.domain.entities.intake_session import IntakeSession


class IntakeSessionRepositoryProtocol(Protocol):
    async def get(self, session_id: str) -> "IntakeSession | None": ...

    async def save(self, session: "IntakeSession") -> None: ...

    async def delete(self, session_id: str) -> bool: ...

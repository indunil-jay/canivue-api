from __future__ import annotations

from app.features.symptom_nlp.domain.entities import IntakeSession
from app.features.symptom_nlp.domain.repositories import IntakeSessionRepositoryProtocol


class InMemoryIntakeSessionRepository(IntakeSessionRepositoryProtocol):
    def __init__(self) -> None:
        self._sessions: dict[str, IntakeSession] = {}

    async def get(self, session_id: str) -> IntakeSession | None:
        return self._sessions.get(session_id)

    async def save(self, session: IntakeSession) -> None:
        self._sessions[session.session_id] = session

    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def clear(self) -> None:
        self._sessions.clear()

from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.domain.entities.vet_profile import VetProfile


class VeterinarianOnboarding:
    """Creates the professional profile behind a veterinarian account."""

    def __init__(self, profiles: VetProfileRepositoryProtocol):
        self._profiles = profiles

    async def veterinarian_registered(
        self, user_id: int, full_name: str | None, verified: bool
    ) -> None:
        await self.ensure_profile(user_id, full_name, verified)

    async def ensure_profile(
        self, user_id: int, full_name: str | None, verified: bool = False
    ) -> VetProfile:
        existing = await self._profiles.get_by_user_id(user_id)
        if existing:
            return existing
        return await self._profiles.create(
            VetProfile(user_id=user_id, name=full_name or "Veterinarian", verified=verified)
        )

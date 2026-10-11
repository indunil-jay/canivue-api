from app.features.veterinarians.application.commands.verify_veterinarian.verify_veterinarian_command import (
    VerifyVeterinarianCommand,
)
from app.features.veterinarians.application.dtos.veterinarian_view import VeterinarianView
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.application.services.veterinarian_views import VeterinarianViews
from app.features.veterinarians.domain.exceptions import VeterinarianNotFoundError
from app.shared.entity import _utc_now


class VerifyVeterinarianCommandHandler:
    def __init__(self, profiles: VetProfileRepositoryProtocol, views: VeterinarianViews):
        self._profiles = profiles
        self._views = views

    async def handle(self, command: VerifyVeterinarianCommand) -> VeterinarianView:
        profile = await self._profiles.get_by_id(command.vet_id)
        if profile is None:
            raise VeterinarianNotFoundError()
        profile.verified = True
        profile.updated_at = _utc_now()
        return await self._views.one(await self._profiles.update(profile))

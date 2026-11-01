from app.features.veterinarians.application.commands.update_my_vet_profile.update_my_vet_profile_command import (
    UpdateMyVetProfileCommand,
)
from app.features.veterinarians.application.dtos.veterinarian_view import VeterinarianView
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.application.services.veterinarian_onboarding import (
    VeterinarianOnboarding,
)
from app.features.veterinarians.application.services.veterinarian_views import VeterinarianViews
from app.shared.entity import _utc_now


class UpdateMyVetProfileCommandHandler:
    def __init__(
        self,
        profiles: VetProfileRepositoryProtocol,
        onboarding: VeterinarianOnboarding,
        views: VeterinarianViews,
    ):
        self._profiles = profiles
        self._onboarding = onboarding
        self._views = views

    async def handle(self, command: UpdateMyVetProfileCommand) -> VeterinarianView:
        profile = await self._onboarding.ensure_profile(command.actor.id, command.actor.name)
        for name, value in command.changes.items():
            setattr(profile, name, value)
        profile.updated_at = _utc_now()
        return await self._views.one(await self._profiles.update(profile))

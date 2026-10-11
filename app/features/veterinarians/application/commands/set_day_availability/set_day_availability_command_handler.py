from app.features.veterinarians.application.commands.set_day_availability.set_day_availability_command import (
    SetDayAvailabilityCommand,
)
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.application.services.veterinarian_onboarding import (
    VeterinarianOnboarding,
)
from app.features.veterinarians.domain.constants import WEEKDAYS
from app.features.veterinarians.domain.exceptions import UnknownWeekdayError
from app.shared.entity import _utc_now


class SetDayAvailabilityCommandHandler:
    def __init__(self, profiles: VetProfileRepositoryProtocol, onboarding: VeterinarianOnboarding):
        self._profiles = profiles
        self._onboarding = onboarding

    async def handle(self, command: SetDayAvailabilityCommand) -> dict[str, bool]:
        if command.day not in WEEKDAYS:
            raise UnknownWeekdayError(command.day)
        profile = await self._onboarding.ensure_profile(command.actor.id, command.actor.name)
        profile.availability = {
            d: command.available if d == command.day else profile.availability.get(d, False)
            for d in WEEKDAYS
        }
        profile.updated_at = _utc_now()
        return (await self._profiles.update(profile)).availability

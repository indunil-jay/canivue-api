from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.features.veterinarians.domain.entities import (
    WEEKDAYS,
    ConsultationType,
    VetProfile,
    VetStats,
)
from app.features.veterinarians.domain.exceptions import (
    UnknownWeekdayError,
    VeterinarianNotFoundError,
)
from app.features.veterinarians.domain.repositories import (
    VetProfileRepositoryProtocol,
    VetStatsProviderProtocol,
)
from app.shared.actor import Actor
from app.shared.entity import _utc_now


@dataclass(frozen=True)
class VeterinarianView:
    profile: VetProfile
    stats: VetStats
    available_today: bool


@dataclass(frozen=True)
class VetSearchFilters:
    query: str = ""
    specialty: str | None = None
    consultation_type: ConsultationType | None = None
    available_today_only: bool = False


class VeterinarianViews:
    def __init__(self, stats: VetStatsProviderProtocol):
        self._stats = stats

    async def of(self, profiles: Sequence[VetProfile]) -> list[VeterinarianView]:
        stats = await self._stats.stats_for([p.id for p in profiles])
        now = datetime.now(timezone.utc)
        return [
            VeterinarianView(p, stats.get(p.id, VetStats()), p.is_available_on(now))
            for p in profiles
        ]

    async def one(self, profile: VetProfile) -> VeterinarianView:
        return (await self.of([profile]))[0]


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


class GetMyVetProfileUseCase:
    def __init__(self, onboarding: VeterinarianOnboarding, views: VeterinarianViews):
        self._onboarding = onboarding
        self._views = views

    async def execute(self, actor: Actor) -> VeterinarianView:
        return await self._views.one(await self._onboarding.ensure_profile(actor.id, actor.name))


class UpdateMyVetProfileUseCase:
    def __init__(
        self,
        profiles: VetProfileRepositoryProtocol,
        onboarding: VeterinarianOnboarding,
        views: VeterinarianViews,
    ):
        self._profiles = profiles
        self._onboarding = onboarding
        self._views = views

    async def execute(self, actor: Actor, changes: dict[str, Any]) -> VeterinarianView:
        profile = await self._onboarding.ensure_profile(actor.id, actor.name)
        for name, value in changes.items():
            setattr(profile, name, value)
        profile.updated_at = _utc_now()
        return await self._views.one(await self._profiles.update(profile))


class SearchVeterinariansUseCase:
    def __init__(self, profiles: VetProfileRepositoryProtocol, views: VeterinarianViews):
        self._profiles = profiles
        self._views = views

    async def execute(self, filters: VetSearchFilters) -> list[VeterinarianView]:
        matching = [
            p
            for p in await self._profiles.list_by_verified(True)
            if p.matches(filters.query)
            and (not filters.specialty or p.has_specialty(filters.specialty))
            and (not filters.consultation_type or p.offers(filters.consultation_type))
        ]
        views = await self._views.of(matching)
        if filters.available_today_only:
            views = [v for v in views if v.available_today]
        return sorted(views, key=lambda v: (-v.stats.rating, v.profile.name))


class GetVeterinarianUseCase:
    def __init__(self, profiles: VetProfileRepositoryProtocol, views: VeterinarianViews):
        self._profiles = profiles
        self._views = views

    async def execute(self, actor: Actor, vet_id: str) -> VeterinarianView:
        profile = await self._profiles.get_by_id(vet_id)
        # Unverified veterinarians are visible only to themselves and administrators.
        if profile is None or not (
            profile.verified or actor.is_admin or profile.user_id == actor.id
        ):
            raise VeterinarianNotFoundError()
        return await self._views.one(profile)


class ListPendingVeterinariansUseCase:
    def __init__(self, profiles: VetProfileRepositoryProtocol, views: VeterinarianViews):
        self._profiles = profiles
        self._views = views

    async def execute(self) -> list[VeterinarianView]:
        return await self._views.of(await self._profiles.list_by_verified(False))


class VerifyVeterinarianUseCase:
    def __init__(self, profiles: VetProfileRepositoryProtocol, views: VeterinarianViews):
        self._profiles = profiles
        self._views = views

    async def execute(self, vet_id: str) -> VeterinarianView:
        profile = await self._profiles.get_by_id(vet_id)
        if profile is None:
            raise VeterinarianNotFoundError()
        profile.verified = True
        profile.updated_at = _utc_now()
        return await self._views.one(await self._profiles.update(profile))


class GetMyAvailabilityUseCase:
    def __init__(self, onboarding: VeterinarianOnboarding):
        self._onboarding = onboarding

    async def execute(self, actor: Actor) -> dict[str, bool]:
        profile = await self._onboarding.ensure_profile(actor.id, actor.name)
        return {day: profile.availability.get(day, False) for day in WEEKDAYS}


class SetDayAvailabilityUseCase:
    def __init__(self, profiles: VetProfileRepositoryProtocol, onboarding: VeterinarianOnboarding):
        self._profiles = profiles
        self._onboarding = onboarding

    async def execute(self, actor: Actor, day: str, available: bool) -> dict[str, bool]:
        if day not in WEEKDAYS:
            raise UnknownWeekdayError(day)
        profile = await self._onboarding.ensure_profile(actor.id, actor.name)
        profile.availability = {
            d: available if d == day else profile.availability.get(d, False) for d in WEEKDAYS
        }
        profile.updated_at = _utc_now()
        return (await self._profiles.update(profile)).availability

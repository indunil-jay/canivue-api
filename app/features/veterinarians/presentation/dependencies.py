from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.veterinarians.application.use_cases import (
    GetMyAvailabilityUseCase,
    GetMyVetProfileUseCase,
    GetVeterinarianUseCase,
    ListPendingVeterinariansUseCase,
    SearchVeterinariansUseCase,
    SetDayAvailabilityUseCase,
    UpdateMyVetProfileUseCase,
    VerifyVeterinarianUseCase,
    VeterinarianOnboarding,
    VeterinarianViews,
)
from app.features.veterinarians.domain.repositories import (
    VetProfileRepositoryProtocol,
    VetStatsProviderProtocol,
)
from app.features.veterinarians.infrastructure.persistence.repositories import (
    NoStatsProvider,
    SqlAlchemyVetProfileRepository,
)


def get_vet_profile_repository(
    session: AsyncSession = Depends(get_db_session),
) -> VetProfileRepositoryProtocol:
    return SqlAlchemyVetProfileRepository(session=session)


def get_vet_stats_provider(
    session: AsyncSession = Depends(get_db_session),
) -> VetStatsProviderProtocol:
    return NoStatsProvider()


def get_veterinarian_views(
    stats: VetStatsProviderProtocol = Depends(get_vet_stats_provider),
) -> VeterinarianViews:
    return VeterinarianViews(stats)


def get_veterinarian_onboarding(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
) -> VeterinarianOnboarding:
    return VeterinarianOnboarding(profiles)


def get_my_vet_profile_use_case(
    onboarding: VeterinarianOnboarding = Depends(get_veterinarian_onboarding),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> GetMyVetProfileUseCase:
    return GetMyVetProfileUseCase(onboarding, views)


def get_update_my_vet_profile_use_case(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    onboarding: VeterinarianOnboarding = Depends(get_veterinarian_onboarding),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> UpdateMyVetProfileUseCase:
    return UpdateMyVetProfileUseCase(profiles, onboarding, views)


def get_search_veterinarians_use_case(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> SearchVeterinariansUseCase:
    return SearchVeterinariansUseCase(profiles, views)


def get_get_veterinarian_use_case(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> GetVeterinarianUseCase:
    return GetVeterinarianUseCase(profiles, views)


def get_list_pending_veterinarians_use_case(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> ListPendingVeterinariansUseCase:
    return ListPendingVeterinariansUseCase(profiles, views)


def get_verify_veterinarian_use_case(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> VerifyVeterinarianUseCase:
    return VerifyVeterinarianUseCase(profiles, views)


def get_my_availability_use_case(
    onboarding: VeterinarianOnboarding = Depends(get_veterinarian_onboarding),
) -> GetMyAvailabilityUseCase:
    return GetMyAvailabilityUseCase(onboarding)


def get_set_day_availability_use_case(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    onboarding: VeterinarianOnboarding = Depends(get_veterinarian_onboarding),
) -> SetDayAvailabilityUseCase:
    return SetDayAvailabilityUseCase(profiles, onboarding)

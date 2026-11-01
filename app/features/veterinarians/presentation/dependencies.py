from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.reviews.infrastructure.services.reputation_stats_provider import (
    ReputationStatsProvider,
)
from app.features.veterinarians.application.commands.set_day_availability.set_day_availability_command_handler import (
    SetDayAvailabilityCommandHandler,
)
from app.features.veterinarians.application.commands.update_my_vet_profile.update_my_vet_profile_command_handler import (
    UpdateMyVetProfileCommandHandler,
)
from app.features.veterinarians.application.commands.verify_veterinarian.verify_veterinarian_command_handler import (
    VerifyVeterinarianCommandHandler,
)
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.application.interfaces.services.vet_stats_provider import (
    VetStatsProviderProtocol,
)
from app.features.veterinarians.application.queries.get_my_availability.get_my_availability_query_handler import (
    GetMyAvailabilityQueryHandler,
)
from app.features.veterinarians.application.queries.get_my_vet_profile.get_my_vet_profile_query_handler import (
    GetMyVetProfileQueryHandler,
)
from app.features.veterinarians.application.queries.get_veterinarian.get_veterinarian_query_handler import (
    GetVeterinarianQueryHandler,
)
from app.features.veterinarians.application.queries.list_pending_veterinarians.list_pending_veterinarians_query_handler import (
    ListPendingVeterinariansQueryHandler,
)
from app.features.veterinarians.application.queries.search_veterinarians.search_veterinarians_query_handler import (
    SearchVeterinariansQueryHandler,
)
from app.features.veterinarians.application.services.veterinarian_onboarding import (
    VeterinarianOnboarding,
)
from app.features.veterinarians.application.services.veterinarian_views import VeterinarianViews
from app.features.veterinarians.infrastructure.persistence.repositories.vet_profile_repository import (
    SqlAlchemyVetProfileRepository,
)


def get_vet_profile_repository(
    session: AsyncSession = Depends(get_db_session),
) -> VetProfileRepositoryProtocol:
    return SqlAlchemyVetProfileRepository(session=session)


def get_vet_stats_provider(
    session: AsyncSession = Depends(get_db_session),
) -> VetStatsProviderProtocol:
    return ReputationStatsProvider(session)


def get_veterinarian_views(
    stats: VetStatsProviderProtocol = Depends(get_vet_stats_provider),
) -> VeterinarianViews:
    return VeterinarianViews(stats)


def get_veterinarian_onboarding(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
) -> VeterinarianOnboarding:
    return VeterinarianOnboarding(profiles)


def get_my_vet_profile_query_handler(
    onboarding: VeterinarianOnboarding = Depends(get_veterinarian_onboarding),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> GetMyVetProfileQueryHandler:
    return GetMyVetProfileQueryHandler(onboarding, views)


def get_update_my_vet_profile_command_handler(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    onboarding: VeterinarianOnboarding = Depends(get_veterinarian_onboarding),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> UpdateMyVetProfileCommandHandler:
    return UpdateMyVetProfileCommandHandler(profiles, onboarding, views)


def get_search_veterinarians_query_handler(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> SearchVeterinariansQueryHandler:
    return SearchVeterinariansQueryHandler(profiles, views)


def get_veterinarian_query_handler(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> GetVeterinarianQueryHandler:
    return GetVeterinarianQueryHandler(profiles, views)


def get_list_pending_veterinarians_query_handler(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> ListPendingVeterinariansQueryHandler:
    return ListPendingVeterinariansQueryHandler(profiles, views)


def get_verify_veterinarian_command_handler(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    views: VeterinarianViews = Depends(get_veterinarian_views),
) -> VerifyVeterinarianCommandHandler:
    return VerifyVeterinarianCommandHandler(profiles, views)


def get_my_availability_query_handler(
    onboarding: VeterinarianOnboarding = Depends(get_veterinarian_onboarding),
) -> GetMyAvailabilityQueryHandler:
    return GetMyAvailabilityQueryHandler(onboarding)


def get_set_day_availability_command_handler(
    profiles: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    onboarding: VeterinarianOnboarding = Depends(get_veterinarian_onboarding),
) -> SetDayAvailabilityCommandHandler:
    return SetDayAvailabilityCommandHandler(profiles, onboarding)

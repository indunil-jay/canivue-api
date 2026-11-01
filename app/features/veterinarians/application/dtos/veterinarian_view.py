from dataclasses import dataclass

from app.features.veterinarians.application.dtos.vet_profile_output_dto import VetProfileOutputDTO
from app.features.veterinarians.domain.value_objects.vet_stats import VetStats


@dataclass(frozen=True)
class VeterinarianView:
    profile: VetProfileOutputDTO
    stats: VetStats
    available_today: bool

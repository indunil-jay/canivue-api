from dataclasses import dataclass

from app.features.veterinarians.domain.entities.vet_profile import VetProfile
from app.features.veterinarians.domain.value_objects.vet_stats import VetStats


@dataclass(frozen=True)
class VeterinarianView:
    profile: VetProfile
    stats: VetStats
    available_today: bool

from dataclasses import dataclass

from app.features.veterinarians.application.dtos.vet_search_filters import VetSearchFilters


@dataclass(frozen=True)
class SearchVeterinariansQuery:
    filters: VetSearchFilters

from dataclasses import dataclass


@dataclass(frozen=True)
class ListVetReviewsQuery:
    vet_id: str

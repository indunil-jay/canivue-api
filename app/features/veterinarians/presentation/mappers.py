from app.features.veterinarians.application.dtos.veterinarian_view import VeterinarianView
from app.features.veterinarians.presentation.responses.veterinarian_response import (
    VeterinarianResponse,
)
from app.shared.text import initials_of


class VeterinariansPresentationMapper:
    @staticmethod
    def to_veterinarian_response(view: VeterinarianView) -> VeterinarianResponse:
        p, s = view.profile, view.stats
        return VeterinarianResponse(
            id=p.id,
            name=p.name,
            initials=initials_of(p.name),
            verified=p.verified,
            specialty=p.specialty,
            specialties=p.specialties,
            experience_years=p.experience_years,
            rating=s.rating,
            review_count=s.review_count,
            consultation_count=s.consultation_count,
            response_time_minutes=p.response_time_minutes,
            consultation_fee_usd=p.consultation_fee_usd,
            languages=p.languages,
            available_today=view.available_today,
            consultation_types=p.consultation_types,
            bio=p.bio,
            clinics=p.clinics,
            qualifications=p.qualifications,
            follow_up_rate_percent=s.follow_up_rate_percent,
            recommendations_accepted_percent=s.recommendations_accepted_percent,
        )

from app.features.assessments.application.dtos.prediction_output_dto import PredictionOutputDTO
from app.features.assessments.domain.entities.prediction import Prediction


class PredictionDTOMapper:
    @staticmethod
    def to_output_dto(entity: Prediction) -> PredictionOutputDTO:
        return PredictionOutputDTO(
            id=entity.id,
            dog_id=entity.dog_id,
            title=entity.title,
            category=entity.category,
            status=entity.status,
            combined_risk_percent=entity.combined_risk_percent,
            confidence_percent=entity.confidence_percent,
            prediction_date=entity.prediction_date,
            model_version=entity.model_version,
            affected_indicators=entity.affected_indicators,
            recommended_next_step=entity.recommended_next_step,
            model_contributions=entity.model_contributions,
            data_quality_note=entity.data_quality_note,
            historical_comparison_note=entity.historical_comparison_note,
            outcome_note=entity.outcome_note,
            image_file_id=entity.image_file_id,
            assessment=entity.assessment,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

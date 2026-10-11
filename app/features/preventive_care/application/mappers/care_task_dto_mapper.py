from app.features.preventive_care.application.dtos.care_task_output_dto import CareTaskOutputDTO
from app.features.preventive_care.domain.entities.care_task import CareTask


class CareTaskDTOMapper:
    @staticmethod
    def to_output_dto(entity: CareTask) -> CareTaskOutputDTO:
        return CareTaskOutputDTO(
            id=entity.id,
            dog_id=entity.dog_id,
            category=entity.category,
            title=entity.title,
            due_date=entity.due_date,
            completed=entity.completed,
            completed_at=entity.completed_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_overdue=entity.is_overdue,
        )

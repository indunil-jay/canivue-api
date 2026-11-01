from app.features.billing.application.dtos.invoice_output_dto import InvoiceOutputDTO
from app.features.billing.domain.entities.invoice import Invoice


class InvoiceDTOMapper:
    @staticmethod
    def to_output_dto(entity: Invoice) -> InvoiceOutputDTO:
        return InvoiceOutputDTO(
            id=entity.id,
            user_id=entity.user_id,
            date=entity.date,
            amount=entity.amount,
            status=entity.status,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

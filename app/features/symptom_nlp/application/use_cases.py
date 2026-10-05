from app.features.symptom_nlp.application.dtos import (
    ParseSymptomInputDTO,
    ParseSymptomOutputDTO,
)
from app.features.symptom_nlp.domain.exceptions import EmptySymptomTextException
from app.features.symptom_nlp.domain.repositories import NLPSymptomEngineProtocol


class ParseSymptomTextUseCase:
    """Use case coordinating symptom text validation and NLP engine parsing."""

    def __init__(self, engine: NLPSymptomEngineProtocol):
        self.engine = engine

    async def execute(self, input_dto: ParseSymptomInputDTO) -> ParseSymptomOutputDTO:
        clean_text = input_dto.text.strip() if input_dto.text else ""
        if not clean_text:
            raise EmptySymptomTextException()

        parse_result = await self.engine.parse(clean_text)
        return ParseSymptomOutputDTO.from_entity(parse_result)

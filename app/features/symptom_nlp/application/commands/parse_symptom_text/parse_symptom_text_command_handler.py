from app.features.symptom_nlp.application.commands.parse_symptom_text.parse_symptom_text_command import (
    ParseSymptomTextCommand,
)
from app.features.symptom_nlp.application.dtos.parse_symptom_output_dto import ParseSymptomOutputDTO
from app.features.symptom_nlp.application.interfaces.services.nlp_symptom_engine import (
    NLPSymptomEngineProtocol,
)
from app.features.symptom_nlp.domain.exceptions import EmptySymptomTextException


class ParseSymptomTextCommandHandler:
    def __init__(self, engine: NLPSymptomEngineProtocol):
        self.engine = engine

    async def handle(self, command: ParseSymptomTextCommand) -> ParseSymptomOutputDTO:
        clean_text = command.text.strip() if command.text else ""
        if not clean_text:
            raise EmptySymptomTextException()

        parse_result = await self.engine.parse(clean_text)
        return ParseSymptomOutputDTO.from_entity(parse_result)

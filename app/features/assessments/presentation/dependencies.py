from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.file_storage import get_file_storage
from app.features.assessments.application.commands.record_prediction_outcome.record_prediction_outcome_command_handler import (
    RecordPredictionOutcomeCommandHandler,
)
from app.features.assessments.application.commands.run_health_check.run_health_check_command_handler import (
    RunHealthCheckCommandHandler,
)
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.application.interfaces.services.fusion_engine import (
    FusionEngineProtocol,
)
from app.features.assessments.application.interfaces.services.symptom_parser import (
    SymptomParserPort,
)
from app.features.assessments.application.queries.get_latest_prediction.get_latest_prediction_query_handler import (
    GetLatestPredictionQueryHandler,
)
from app.features.assessments.application.queries.get_prediction.get_prediction_query_handler import (
    GetPredictionQueryHandler,
)
from app.features.assessments.application.queries.list_predictions.list_predictions_query_handler import (
    ListPredictionsQueryHandler,
)
from app.features.assessments.infrastructure.ml.engine import StubFusionEngine
from app.features.assessments.infrastructure.persistence.repositories.prediction_repository import (
    SqlAlchemyPredictionRepository,
)
from app.features.assessments.infrastructure.services.symptom_nlp_parser import SymptomNlpParser
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.health_metrics.application.interfaces.repositories.metric_reading_repository import (
    MetricReadingRepositoryProtocol,
)
from app.features.health_metrics.presentation.dependencies import get_metric_reading_repository
from app.features.notifications.presentation.dependencies import get_notifier
from app.features.symptom_nlp.application.use_cases import ParseSymptomTextUseCase
from app.features.symptom_nlp.presentation.dependencies import get_parse_symptom_use_case
from app.shared.files import FileStorageProtocol
from app.shared.notifier import NotifierProtocol

_fusion_engine = StubFusionEngine()


def get_fusion_engine() -> FusionEngineProtocol:
    # No trained fusion model exists yet, so USE_REAL_ML_MODELS has nothing to switch to here.
    return _fusion_engine


def get_symptom_parser(
    parse_use_case: ParseSymptomTextUseCase = Depends(get_parse_symptom_use_case),
) -> SymptomParserPort:
    return SymptomNlpParser(parse_use_case)


def get_prediction_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PredictionRepositoryProtocol:
    return SqlAlchemyPredictionRepository(session=session)


def get_run_health_check_command_handler(
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    readings: MetricReadingRepositoryProtocol = Depends(get_metric_reading_repository),
    access: DogAccess = Depends(get_dog_access),
    engine: FusionEngineProtocol = Depends(get_fusion_engine),
    parser: SymptomParserPort = Depends(get_symptom_parser),
    storage: FileStorageProtocol = Depends(get_file_storage),
    notifier: NotifierProtocol = Depends(get_notifier),
) -> RunHealthCheckCommandHandler:
    return RunHealthCheckCommandHandler(
        predictions, readings, access, engine, parser, storage, notifier
    )


def get_list_predictions_query_handler(
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    access: DogAccess = Depends(get_dog_access),
) -> ListPredictionsQueryHandler:
    return ListPredictionsQueryHandler(predictions, access)


def get_latest_prediction_query_handler(
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    access: DogAccess = Depends(get_dog_access),
) -> GetLatestPredictionQueryHandler:
    return GetLatestPredictionQueryHandler(predictions, access)


def get_prediction_query_handler(
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    access: DogAccess = Depends(get_dog_access),
) -> GetPredictionQueryHandler:
    return GetPredictionQueryHandler(predictions, access)


def get_record_prediction_outcome_command_handler(
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    access: DogAccess = Depends(get_dog_access),
) -> RecordPredictionOutcomeCommandHandler:
    return RecordPredictionOutcomeCommandHandler(predictions, access)

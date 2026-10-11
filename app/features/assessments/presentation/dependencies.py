from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.file_storage import get_file_storage
from app.features.assessments.application.use_cases import (
    GetLatestPredictionUseCase,
    GetPredictionUseCase,
    ListPredictionsUseCase,
    RecordPredictionOutcomeUseCase,
    RunHealthCheckUseCase,
    SymptomParserPort,
)
from app.features.assessments.domain.entities import (
    FusionEngineProtocol,
    PredictionRepositoryProtocol,
)
from app.features.assessments.infrastructure.ml.engine import StubFusionEngine
from app.features.assessments.infrastructure.persistence.repositories import (
    SqlAlchemyPredictionRepository,
)
from app.features.assessments.infrastructure.symptom_parser import SymptomNlpParser
from app.features.dogs.application.access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.health_metrics.domain.entities import MetricReadingRepositoryProtocol
from app.features.health_metrics.presentation.router import get_metric_reading_repository
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


def get_run_health_check_use_case(
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    readings: MetricReadingRepositoryProtocol = Depends(get_metric_reading_repository),
    access: DogAccess = Depends(get_dog_access),
    engine: FusionEngineProtocol = Depends(get_fusion_engine),
    parser: SymptomParserPort = Depends(get_symptom_parser),
    storage: FileStorageProtocol = Depends(get_file_storage),
    notifier: NotifierProtocol = Depends(get_notifier),
) -> RunHealthCheckUseCase:
    return RunHealthCheckUseCase(predictions, readings, access, engine, parser, storage, notifier)


def get_list_predictions_use_case(
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    access: DogAccess = Depends(get_dog_access),
) -> ListPredictionsUseCase:
    return ListPredictionsUseCase(predictions, access)


def get_latest_prediction_use_case(
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    access: DogAccess = Depends(get_dog_access),
) -> GetLatestPredictionUseCase:
    return GetLatestPredictionUseCase(predictions, access)


def get_get_prediction_use_case(
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    access: DogAccess = Depends(get_dog_access),
) -> GetPredictionUseCase:
    return GetPredictionUseCase(predictions, access)


def get_record_prediction_outcome_use_case(
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    access: DogAccess = Depends(get_dog_access),
) -> RecordPredictionOutcomeUseCase:
    return RecordPredictionOutcomeUseCase(predictions, access)

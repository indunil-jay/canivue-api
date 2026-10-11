from datetime import datetime, timezone

from app.features.dogs.application.services.dog_access import DogAccess
from app.features.health_metrics.application.commands.record_readings.record_readings_command import (
    RecordReadingsCommand,
)
from app.features.health_metrics.application.interfaces.repositories.metric_reading_repository import (
    MetricReadingRepositoryProtocol,
)
from app.features.health_metrics.domain.entities.metric_reading import MetricReading


class RecordReadingsCommandHandler:
    def __init__(self, readings: MetricReadingRepositoryProtocol, access: DogAccess):
        self._readings = readings
        self._access = access

    async def handle(self, command: RecordReadingsCommand) -> int:
        dog = await self._access.owned(command.actor, command.dog_id)
        now = datetime.now(timezone.utc)
        readings = []
        for value, recorded_at in command.values:
            when = recorded_at or now
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            reading = MetricReading(
                dog_id=dog.id, metric=command.metric, value=value, recorded_at=when
            )
            reading.validate(now)
            readings.append(reading)
        await self._readings.add_many(readings)
        return len(readings)

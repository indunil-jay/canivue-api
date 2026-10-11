from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class SyncCollarCommand:
    actor: Actor
    dog_id: str
    records_synced: int
    battery_percent: int | None

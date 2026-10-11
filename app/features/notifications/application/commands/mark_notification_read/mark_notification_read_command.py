from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class MarkNotificationReadCommand:
    actor: Actor
    notification_id: str

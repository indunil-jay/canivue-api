from dataclasses import dataclass


@dataclass(frozen=True)
class VitalsSnapshot:
    heart_rate_bpm: int | None
    temperature_c: float | None
    activity_steps_today: int
    activity_goal_steps: int
    sleep_hours_last_night: float | None
    hydration_ml: int
    hydration_goal_ml: int
    weight_kg: float

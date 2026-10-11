from app.features.veterinarians.domain.constants import WEEKDAYS


def default_availability() -> dict[str, bool]:
    return {day: day not in ("Saturday", "Sunday") for day in WEEKDAYS}

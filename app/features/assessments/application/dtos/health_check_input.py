from dataclasses import dataclass


@dataclass(frozen=True)
class HealthCheckInput:
    dog_id: str
    symptom_text: str = ""
    use_sensor_data: bool = False
    image: bytes | None = None
    image_content_type: str | None = None
    max_image_bytes: int = 0

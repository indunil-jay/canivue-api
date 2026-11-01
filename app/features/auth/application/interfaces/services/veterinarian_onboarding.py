from typing import Protocol


class VeterinarianOnboardingPort(Protocol):
    """Lets the module that owns professional profiles react to a new veterinarian account."""

    async def veterinarian_registered(
        self, user_id: int, full_name: str | None, verified: bool
    ) -> None: ...

from dataclasses import dataclass

from app.shared.text import initials_of


@dataclass(frozen=True)
class Actor:
    id: int
    role: str
    name: str | None = None
    email: str = ""

    @property
    def is_admin(self) -> bool:
        return self.role == "ADMIN"

    @property
    def is_vet(self) -> bool:
        return self.role == "VET"

    @property
    def display_name(self) -> str:
        return self.name or self.email.split("@")[0] or "User"

    @property
    def initials(self) -> str:
        return initials_of(self.display_name)

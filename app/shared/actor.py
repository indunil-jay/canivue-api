from dataclasses import dataclass


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
        parts = [p for p in self.display_name.replace(".", " ").split() if p.lower() != "dr"]
        return "".join(p[0] for p in parts[:2]).upper() or "U"

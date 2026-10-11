from dataclasses import asdict, dataclass, fields, replace


@dataclass(frozen=True)
class PrivacySettings:
    share_with_vet: bool = True
    share_anonymized_research: bool = False
    location_services: bool = False
    two_factor_enabled: bool = False

    def updated(self, changes: dict[str, bool]) -> "PrivacySettings":
        known = {f.name for f in fields(self)}
        return replace(self, **{k: bool(v) for k, v in changes.items() if k in known})

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> "PrivacySettings":
        return cls().updated(data or {})

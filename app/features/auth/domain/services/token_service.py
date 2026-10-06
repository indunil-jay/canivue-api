from abc import ABC, abstractmethod


class TokenService(ABC):
    """Abstract interface for token encoding, decoding, and life-cycle services."""

    @abstractmethod
    def create_access_token(self, subject: str, role: str) -> str: ...

    @abstractmethod
    def create_refresh_token(self, subject: str) -> str: ...

    @abstractmethod
    def decode_token(self, token: str) -> dict: ...

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """Abstract interface for secure password hashing and verification services."""

    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool: ...


class TokenService(ABC):
    """Abstract interface for token encoding, decoding, and life-cycle services."""

    @abstractmethod
    def create_access_token(self, subject: str, role: str) -> str: ...

    @abstractmethod
    def create_refresh_token(self, subject: str) -> str: ...

    @abstractmethod
    def decode_token(self, token: str) -> dict: ...

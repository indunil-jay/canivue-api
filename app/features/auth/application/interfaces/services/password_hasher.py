from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """Abstract interface for password hashing and verification services."""

    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool: ...

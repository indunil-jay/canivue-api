from abc import ABC, abstractmethod


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, subject: str, role: str) -> str: ...

    @abstractmethod
    def create_refresh_token(self, subject: str) -> str: ...

    @abstractmethod
    def decode_token(self, token: str) -> dict: ...

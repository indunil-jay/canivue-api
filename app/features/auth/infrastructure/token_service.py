from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.features.auth.domain.exceptions import TokenExpiredOrRevokedError
from app.features.auth.domain.services import TokenService


class JwtTokenService(TokenService):
    """Production JWT service using PyJWT."""

    def __init__(
        self,
        secret_key: str = settings.SECRET_KEY,
        access_token_expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days: int = settings.REFRESH_TOKEN_EXPIRE_DAYS,
        algorithm: str = "HS256",
    ):
        self._secret_key = secret_key
        self._access_token_expire_minutes = access_token_expire_minutes
        self._refresh_token_expire_days = refresh_token_expire_days
        self._algorithm = algorithm

    def create_access_token(self, subject: str, role: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(subject),
            "role": role,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._access_token_expire_minutes)).timestamp()),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(self, subject: str) -> str:
        import uuid

        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(subject),
            "jti": str(uuid.uuid4()),
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=self._refresh_token_expire_days)).timestamp()),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return payload
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredOrRevokedError("Token has expired.") from e
        except jwt.PyJWTError as e:
            raise TokenExpiredOrRevokedError("Invalid token.") from e

    @staticmethod
    def hash_token(token: str) -> str:
        import hashlib

        return hashlib.sha256(token.encode("utf-8")).hexdigest()

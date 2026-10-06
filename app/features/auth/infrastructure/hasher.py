from pwdlib import PasswordHash

from app.features.auth.domain.protocols import PasswordHasherProtocol


class Argon2PasswordHasher(PasswordHasherProtocol):
    """Production password hasher using pwdlib with Argon2 / Bcrypt recommendation."""

    def __init__(self):
        # Uses recommended algorithms (argon2 by default)
        self._hasher = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self._hasher.verify(plain_password, hashed_password)

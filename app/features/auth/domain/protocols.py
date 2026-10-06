from app.features.auth.domain.repositories import (
    RbacRepository,
    RefreshTokenRepository,
    UserRepository,
)
from app.features.auth.domain.services import (
    PasswordHasher,
    TokenService,
)

# Aliases for backward compatibility
UserRepositoryProtocol = UserRepository
RefreshTokenRepositoryProtocol = RefreshTokenRepository
RbacRepositoryProtocol = RbacRepository
PasswordHasherProtocol = PasswordHasher
TokenServiceProtocol = TokenService

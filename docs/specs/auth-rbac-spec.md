# Specification: Authentication and Role-Based Access Control (RBAC)

**Status**: Ready for Agent (`ready-for-agent`)  
**Domain Area**: Security, Identity, and Authorization  
**Target Feature**: `app/features/auth/`  

---

## Problem Statement

Currently, the Canivue API lacks an authentication and authorization layer. All incoming HTTP requests to endpoints are unauthenticated and untrusted. Without identity verification and role-based access control, sensitive veterinary medical assessments, dog health profiles, and owner data cannot be safeguarded. Furthermore, different categories of system users—administrators, veterinarians, and dog owners/clients—have vastly different operational privileges. Without robust access control, clients could access clinical records or other owners' data, and unauthorized actors could trigger diagnostics or alter system settings.

---

## Solution

Implement a modular, Clean-Architecture-compliant authentication and authorization feature module under `app/features/auth/`. The solution provides:
1. **JWT-Based Authentication**: Secure OAuth2 password flow issuing short-lived access tokens (15–30 minutes) and long-lived refresh tokens (7–30 days) with token family rotation and revocation tracking.
2. **Role-Based Access Control (RBAC) with Granular Database-Backed Permissions**: Three core roles (`ADMIN`, `VET`, `CLIENT`) mapped to dynamic, database-persisted permissions (e.g., `dogs:read`, `dogs:write`, `assessments:create`, `assessments:review`, `users:manage`).
3. **Composable FastAPI Security Seams**: Dependency guards (`get_current_user`, `require_roles`, `require_permissions`) allowing declarative endpoint protection across all current and future feature routers.
4. **Initial Default RBAC Seeding**: Automated or migration-driven seeding establishing default permissions and role-permission matrices.

---

## User Stories

1. As a new dog owner (client), I want to register an account using my email and password, so that I can manage my dogs and access the platform.
2. As a client, I want my newly registered account to default strictly to the `CLIENT` role, so that I cannot access administrative or veterinary privileges without authorization.
3. As a registered user, I want to log in using my email and password, so that I receive an access token and a refresh token along with my user profile and granted permissions.
4. As an API client, I want to authenticate subsequent requests by including `Authorization: Bearer <access_token>`, so that protected endpoints can verify my identity.
5. As an API client, I want to exchange a valid refresh token at `/api/v1/auth/refresh` for a new access token and a rotated refresh token, so that I maintain continuous session access without re-entering credentials.
6. As a security administrator, I want old refresh tokens to be immediately revoked and tracked upon rotation, so that token theft and replay attacks are mitigated.
7. As an authenticated user, I want to query `/api/v1/auth/me`, so that I can inspect my active identity, role, and granted permissions list.
8. As a veterinarian, I want to be assigned the `VET` role, so that I can review assessments, record clinical observations, and access diagnostic tools unavailable to standard clients.
9. As an administrator, I want to be able to create or onboard veterinary (`VET`) and administrator (`ADMIN`) accounts, so that staff access is strictly controlled.
10. As an administrator, I want to manage roles and permission assignments in the database, so that permissions can be customized as new features are added.
11. As a developer building a feature endpoint, I want to declare `Depends(require_permissions("assessments:review"))`, so that users lacking this permission automatically receive an HTTP 403 Forbidden response.
12. As a developer building a feature endpoint, I want to declare `Depends(require_roles(Role.ADMIN))`, so that only administrators can execute administrative operations.
13. As an authenticated user attempting an action outside my permission set, I want clear and standardized error responses, so that I understand why access was denied.
14. As a user providing invalid credentials at login, I want an HTTP 401 Unauthorized response with safe error messaging, so that account enumerations and unauthorized logins are prevented.

---

## Implementation Decisions

### 1. Architecture and Module Boundaries
- The auth feature will reside in `app/features/auth/` adhering strictly to Clean Architecture:
  - `domain/`: Pure business entities (`User`, `Role`, `Permission`, `RefreshToken`), custom exceptions (`InvalidCredentialsError`, `AccountDisabledError`, `InsufficientPermissionsError`, `TokenExpiredOrRevokedError`), and protocol abstractions (`UserRepositoryProtocol`, `RefreshTokenRepositoryProtocol`, `TokenServiceProtocol`, `PasswordHasherProtocol`). Zero web or framework imports.
  - `application/`: Input/Output DTOs and single-responsibility use cases (`RegisterClientUseCase`, `LoginUseCase`, `RefreshTokenUseCase`, `GetCurrentUserUseCase`, `CreateStaffUserUseCase`, `AssignPermissionsUseCase`).
  - `infrastructure/`: SQLAlchemy models (`UserModel`, `RoleModel`, `PermissionModel`, `RolePermissionModel`, `RefreshTokenModel`), concrete repository implementations (`SqlAlchemyUserRepository`, `SqlAlchemyRefreshTokenRepository`), password hasher adapter (`Argon2` or `Bcrypt`), and JWT adapter.
  - `presentation/`: FastAPI router (`/api/v1/auth/*`), Pydantic v2 request/response schemas, and dependency injectors (`get_current_user`, `require_roles`, `require_permissions`).

### 2. Domain Data Models and Roles
- **Roles**: Enum consisting of:
  - `ADMIN`: Platform administration and staff management.
  - `VET`: Veterinarian clinical workflows and assessment reviews.
  - `CLIENT`: Dog owner actions (dog registration, self-assessments).
- **Permissions**: String keys formatted as `<resource>:<action>` (e.g. `dogs:read`, `dogs:create`, `assessments:create`, `assessments:review`, `users:manage`).
- **Database Schema**:
  - `users`: `id` (UUID/int), `email` (unique index), `hashed_password`, `role` (enum/string), `is_active` (bool), `created_at`, `updated_at`.
  - `permissions`: `id`, `name` (unique string, e.g., `assessments:review`), `description`.
  - `role_permissions`: Association table mapping `role` to `permission_id`.
  - `refresh_tokens`: `id`, `user_id` (foreign key), `token_hash` (unique), `expires_at`, `revoked` (bool), `created_at`.

### 3. Token Strategy and Cryptography
- **Password Hashing**: `passlib` with `bcrypt` or `pwdlib` using `argon2`.
- **JWT Access Token**:
  - Expiry: 15 to 30 minutes.
  - Payload claims: `sub` (User ID), `role`, `exp`, `iat`, `type="access"`.
  - Cryptography: HMAC-SHA256 using `settings.SECRET_KEY`.
- **Refresh Token Lifecycle**:
  - Expiry: 7 to 30 days.
  - Stored hashed in the `refresh_tokens` table.
  - Rotation: When `/refresh` is invoked with a valid refresh token, the existing token is marked `revoked=True` and a new access/refresh token pair is issued.

### 4. Authorization Enforcement Mechanism
- Dependency seam `get_current_user`: Extracts Bearer token from `Authorization` header, decodes JWT, queries user from DB with associated role and permissions, and raises HTTP 401 if invalid or inactive.
- Dependency seam `require_permissions(*required_permissions)`: Reusable FastAPI dependency factory verifying that the authenticated user possesses all specified permissions. Raises HTTP 403 if missing.
- Dependency seam `require_roles(*required_roles)`: Verifies user role matches allowed roles. Raises HTTP 403 if disallowed.

### 5. Seeding Strategy
- Provide a database seed utility (`app/features/auth/infrastructure/seed.py` or Alembic migration) establishing:
  - Default permissions catalog.
  - Default role-to-permission mapping (`CLIENT`, `VET`, `ADMIN`).
  - Optional initial admin setup mechanism.

---

## Testing Decisions

### 1. High-Level Seam Testing
All feature functionality will be tested against public seams:
- **HTTP Seam (`tests/features/auth/test_auth_api.py`)**:
  - End-to-end endpoint tests using `httpx.AsyncClient` and `tests/conftest.py`'s `client` fixture with transactional SQLite in-memory DB.
  - Covers: Client registration, login, token refresh, token revocation on reuse, accessing `/me`, and accessing role/permission-protected test routes.
- **Application Seam (`tests/features/auth/test_use_cases.py`)**:
  - Direct execution of use cases (`LoginUseCase`, `RegisterClientUseCase`, `RefreshTokenUseCase`) with in-memory/mock repository adapters to verify domain logic and exception propagation without HTTP overhead.

### 2. Prior Art
- Existing symptom NLP feature tests (`tests/features/symptom_nlp/`) and the async fixture setup in `tests/conftest.py`.

---

## Out of Scope

- Third-party social logins (Google, Apple OAuth).
- Multi-factor authentication (MFA / 2FA SMS/TOTP).
- Email verification / password reset email dispatch via external SMTP/SendGrid (stubbed or deferred to a dedicated notification service).
- Organization/clinic multi-tenancy partitioning.

---

## Further Notes

- Configuration settings will be extended in `app/config.py`:
  - `ACCESS_TOKEN_EXPIRE_MINUTES: int = 30`
  - `REFRESH_TOKEN_EXPIRE_DAYS: int = 14`
- Endpoints will be mounted in `app/main.py` under the API router at prefix `/api/v1/auth`.

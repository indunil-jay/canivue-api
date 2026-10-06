# Specification: Password Recovery & Google OAuth Authentication

**Status**: Ready for Agent (`ready-for-agent`)  
**Domain Area**: Security, Identity, and Authentication  
**Target Feature**: `app/features/auth/`  

---

## Problem Statement

Users of the Canivue API who forget their passwords currently have no automated recovery path and are permanently locked out of their accounts unless an administrator intervenes manually. Additionally, mobile and web users expect modern, seamless one-tap onboarding and sign-in experiences via Google OAuth 2.0 without having to invent or remember another password. Without password recovery and social authentication, user adoption and retention are severely hindered, and security is compromised when users resort to weak or repeated passwords.

---

## Solution

Extend `app/features/auth/` following Feature-Based Clean Architecture and CQRS to support:
1. **Password Recovery Workflow (Forgot Password & Reset Password)**:
   - A secure, rate-limited request initiated via `POST /api/v1/auth/forgot-password`.
   - Generation of high-entropy, cryptographically secure password reset tokens stored as SHA-256 hashes in a dedicated `password_reset_tokens` table with strict expiration windows (e.g., 15 minutes) and single-use invalidation.
   - Dispatch of recovery emails through an abstracted `EmailService` port (backed by a development logging stub and production-ready interface).
   - Consummation of password reset via `POST /api/v1/auth/reset-password` using the token, updating the user's password hash and revoking existing active refresh tokens.
2. **Google OAuth 2.0 Sign-In & Onboarding**:
   - Client-side token exchange via `POST /api/v1/auth/oauth/google`, accepting a Google ID token.
   - Verification of Google ID token claims (`sub`, `email`, `email_verified`, `name`) via an abstracted `GoogleAuthService` port.
   - Automatic identity linking: if an existing user matches the verified Google email, link the Google subject ID; if no account exists, auto-provision a new user with `CLIENT` role and nullable password.
   - Issuance of standard Canivue access and refresh tokens identical to the standard login pipeline.

---

## User Stories

1. As a registered user who forgot my password, I want to submit my email address to `/api/v1/auth/forgot-password`, so that I receive a secure password reset link or token via email.
2. As a user requesting a password reset, I want the API response to return a generic success message even if my email is not registered, so that attackers cannot enumerate existing account emails.
3. As a user who received a password reset link, I want to submit the reset token and a new strong password to `/api/v1/auth/reset-password`, so that my account password is updated.
4. As a security administrator, I want password reset tokens to expire after 15 minutes, so that the window for token interception is tightly bounded.
5. As a security administrator, I want password reset tokens to be stored strictly as SHA-256 hashes in the database, so that database breaches do not expose usable reset tokens.
6. As a security administrator, I want password reset tokens to be invalidated immediately upon use, so that replay attacks are prevented.
7. As an authenticated user resetting my password, I want all my existing active refresh tokens to be revoked, so that sessions on compromised or lost devices are terminated.
8. As a user resetting my password, I want password complexity rules enforced (minimum 8 characters), so that my account cannot be updated with a weak password.
9. As a mobile or web user with a Google account, I want to sign in using Google at `/api/v1/auth/oauth/google` with my Google ID token, so that I can access Canivue without manually creating a password.
10. As a first-time user signing in with Google, I want an account automatically created with the `CLIENT` role and my Google profile details (name, email), so that I can immediately start registering my dogs.
11. As an existing password user whose Google account uses the same email address, I want my Google identity linked to my existing account upon Google sign-in, so that I don't create a duplicate profile or lose my existing dog records.
12. As a user signing in with an unverified Google account, I want the API to reject the sign-in with an Unauthorized error, so that unauthorized email impersonation is prevented.
13. As an API client consuming `/api/v1/auth/oauth/google`, I want to receive the standard `LoginResponseData` envelope containing `access_token`, `refresh_token`, and the `UserResponseData` profile, so that the client handles OAuth logins identically to password logins.
14. As a developer running tests or local development, I want password reset emails logged to standard logs/console via a stub email provider, so that I don't need live SMTP credentials to test the flow.
15. As a developer running automated tests, I want a stub `GoogleAuthService` capable of verifying test Google tokens without calling external Google servers, so that test suites remain deterministic, offline-capable, and fast.

---

## Implementation Decisions

### 1. CQRS Command & Query Slices
Add discrete command slices adhering to the feature architecture:
- `app/features/auth/application/commands/forgot_password/`:
  - `forgot_password_command.py` (`ForgotPasswordCommand(email: str)`)
  - `forgot_password_command_handler.py` (`ForgotPasswordCommandHandler`)
- `app/features/auth/application/commands/reset_password/`:
  - `reset_password_command.py` (`ResetPasswordCommand(token: str, new_password: str)`)
  - `reset_password_command_handler.py` (`ResetPasswordCommandHandler`)
- `app/features/auth/application/commands/oauth_google/`:
  - `google_login_command.py` (`GoogleLoginCommand(id_token: str)`)
  - `google_login_command_handler.py` (`GoogleLoginCommandHandler`)

### 2. Domain & Application Events
- Domain events under `domain/events/`:
  - `password_reset_requested.py`: `PasswordResetRequestedDomainEvent(user_id: int, email: str, token: str, occurred_at: datetime)`
  - `password_reset_completed.py`: `PasswordResetCompletedDomainEvent(user_id: int, occurred_at: datetime)`
  - `google_user_authenticated.py`: `GoogleUserAuthenticatedDomainEvent(user_id: int, email: str, is_new_user: bool, occurred_at: datetime)`
- Event handlers under `application/event_handlers/`:
  - `send_password_reset_email_handler.py` (delivers email via `EmailService`)

### 3. Outbound Technical Ports (Interfaces)
- `application/interfaces/repositories/password_reset_token_repository.py`:
  - `PasswordResetTokenRepository` protocol:
    - `create(token: PasswordResetToken) -> PasswordResetToken`
    - `get_by_hash(token_hash: str) -> PasswordResetToken | None`
    - `mark_as_used(token_hash: str) -> None`
    - `invalidate_all_for_user(user_id: int) -> None`
- `application/interfaces/services/email_service.py`:
  - `EmailService` protocol: `send_password_reset_email(to_email: str, reset_token: str) -> None`
- `application/interfaces/services/google_auth_service.py`:
  - `GoogleAuthService` protocol: `verify_id_token(id_token: str) -> GoogleProfileDTO`

### 4. Database Schema Changes & Entities
- Add `PasswordResetToken` domain entity in `domain/entities/password_reset_token.py`
- Add `PasswordResetTokenModel` in `infrastructure/models.py`:
  - `id`: Integer primary key
  - `user_id`: Integer foreign key / index
  - `token_hash`: String(64) unique index
  - `expires_at`: DateTime(timezone=True)
  - `is_used`: Boolean (default False)
  - `created_at`: DateTime(timezone=True)
- Update `UserModel`:
  - `hashed_password`: Make nullable (`Mapped[str | None]`) to support OAuth-only accounts
  - `google_id`: String(255) nullable unique index for linked Google accounts

### 5. Concrete Adapters
- `infrastructure/repositories/password_reset_token_repository.py`: `SqlAlchemyPasswordResetTokenRepository`
- `infrastructure/services/email_service.py`: `LoggingEmailService` (logs reset links/tokens; extensible to SMTP)
- `infrastructure/services/google_auth_service.py`: `GoogleTokenVerifierService` (with `StubGoogleAuthService` for offline tests)

### 6. Presentation Layer Endpoints & Contracts
- `POST /api/v1/auth/forgot-password`:
  - Request: `ForgotPasswordRequest(email: EmailStr)`
  - Response: `APIResponse(success=True, message="If that email is registered, a password reset link has been sent.")`
- `POST /api/v1/auth/reset-password`:
  - Request: `ResetPasswordRequest(token: str, new_password: str)`
  - Response: `APIResponse(success=True, message="Password has been reset successfully.")`
- `POST /api/v1/auth/oauth/google`:
  - Request: `GoogleLoginRequest(id_token: str)`
  - Response: `APIResponse[LoginResponseData]`

### 7. Error Handling & Exceptions
Utilize standard `ErrorType`:
- `InvalidResetTokenError` (`ErrorType.VALIDATION` or `ErrorType.UNAUTHORIZED`, 400/401)
- `ResetTokenExpiredError` (`ErrorType.UNAUTHORIZED`, 401)
- `GoogleAuthFailedError` (`ErrorType.UNAUTHORIZED`, 401)

---

## Testing Decisions

- **Black-Box Testing at HTTP Seam**: Tests execute against FastAPI endpoints (`/api/v1/auth/forgot-password`, `/api/v1/auth/reset-password`, `/api/v1/auth/oauth/google`) via `httpx.AsyncClient`.
- **Test Scenarios**:
  - `test_forgot_password_existing_user`: Dispatches reset email via stub and persists hashed token.
  - `test_forgot_password_nonexistent_user`: Returns generic 200 OK without disclosing user absence.
  - `test_reset_password_success`: Resets password, verifies login with new password, and verifies old password fails.
  - `test_reset_password_revokes_active_refresh_tokens`: Existing refresh tokens invalidated upon reset.
  - `test_reset_password_expired_token`: Fails with 401 Unauthorized.
  - `test_reset_password_reused_token`: Attempting to use the same token twice fails.
  - `test_google_oauth_new_user_provisioning`: Automatically creates user with `Role.CLIENT`, null password, and returns valid token pair.
  - `test_google_oauth_existing_user_linking`: Correctly links and logs in existing user by email.
  - `test_google_oauth_invalid_or_unverified_token`: Fails with 401 Unauthorized.

---

## Out of Scope

- Apple Sign-In / Microsoft OAuth (future spec).
- Real SMTP server configuration or cloud delivery vendors (SendGrid/Resend) in unit test runs.
- SMS-based OTP two-factor authentication.
- CAPTCHA or Cloudflare Turnstile bot detection (handled at API Gateway level).

---

## Further Notes

- Maintains zero third-party framework leakage into `domain/`.
- Maintains strict CQRS folder and naming conventions without barrel `__init__.py` files.

import pytest

from app.core.exceptions import ConflictException, ValidationException
from app.features.auth.application.dtos import RegisterClientInputDTO
from app.features.auth.application.use_cases import RegisterClientUseCase
from app.features.auth.domain.entities import Role, User
from app.features.auth.domain.protocols import PasswordHasherProtocol, UserRepositoryProtocol


class FakeUserRepository(UserRepositoryProtocol):
    def __init__(self):
        self._users = {}
        self._id_counter = 1

    async def get_by_id(self, user_id: int):
        return self._users.get(user_id)

    async def get_by_email(self, email: str):
        for user in self._users.values():
            if user.email == email.lower():
                return user
        return None

    async def create(self, user: User) -> User:
        user.id = self._id_counter
        self._id_counter += 1
        self._users[user.id] = user
        return user

    async def update(self, user: User) -> User:
        self._users[user.id] = user
        return user


class FakePasswordHasher(PasswordHasherProtocol):
    def hash(self, password: str) -> str:
        return f"hashed_{password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed_{plain_password}"


@pytest.mark.asyncio
async def test_register_client_use_case_success():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    use_case = RegisterClientUseCase(user_repo=repo, hasher=hasher)

    dto = RegisterClientInputDTO(
        email="client@example.com",
        password="securePassword123",
        full_name="Jane Doe",
    )
    result = await use_case.execute(dto)

    assert result.id == 1
    assert result.email == "client@example.com"
    assert result.role == Role.CLIENT
    assert result.full_name == "Jane Doe"
    assert result.is_active is True


@pytest.mark.asyncio
async def test_register_client_use_case_duplicate_email():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    use_case = RegisterClientUseCase(user_repo=repo, hasher=hasher)

    dto = RegisterClientInputDTO(email="client@example.com", password="securePassword123")
    await use_case.execute(dto)

    with pytest.raises(ConflictException):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_register_client_use_case_invalid_password():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    use_case = RegisterClientUseCase(user_repo=repo, hasher=hasher)

    dto = RegisterClientInputDTO(email="client@example.com", password="short")
    with pytest.raises(ValidationException):
        await use_case.execute(dto)

from typing import Protocol


class EmailService(Protocol):
    async def send_password_reset_email(self, to_email: str, reset_token: str) -> None: ...

    async def send_verification_code_email(self, to_email: str, code: str) -> None: ...

import logging

from app.features.auth.application.interfaces.services.email_service import (
    EmailService,
)

logger = logging.getLogger("canivue.auth.email")


class LoggingEmailService(EmailService):
    def __init__(self):
        self.sent_emails: list[dict[str, str]] = []

    async def send_password_reset_email(self, to_email: str, reset_token: str) -> None:
        self.sent_emails.append({"to": to_email, "token": reset_token})
        logger.info(
            "Password reset email sent to %s with token: %s",
            to_email,
            reset_token,
        )

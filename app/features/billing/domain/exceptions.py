from app.core.exceptions import AppException, NotFoundException


class PlanNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Subscription plan not found.")


class PaymentFailedError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Payment was declined. Your plan has not changed.", status_code=402
        )

from app.features.billing.application.interfaces.services.payment_gateway import (
    PaymentGatewayProtocol,
)


class StubPaymentGateway(PaymentGatewayProtocol):
    """Stands in for a payment provider: every charge succeeds and no money moves."""

    async def charge(self, user_id: int, amount: float, description: str) -> bool:
        return True

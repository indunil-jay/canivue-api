from typing import Protocol


class PaymentGatewayProtocol(Protocol):
    async def charge(self, user_id: int, amount: float, description: str) -> bool:
        """Takes payment. Returns whether it succeeded."""
        ...

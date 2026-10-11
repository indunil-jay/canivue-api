from app.features.billing.application.dtos.current_subscription import CurrentSubscription
from app.features.billing.application.queries.get_current_subscription.get_current_subscription_query import (
    GetCurrentSubscriptionQuery,
)
from app.features.billing.application.services.current_subscriptions import CurrentSubscriptions


class GetCurrentSubscriptionQueryHandler:
    def __init__(self, subscriptions: CurrentSubscriptions):
        self._subscriptions = subscriptions

    async def handle(self, query: GetCurrentSubscriptionQuery) -> CurrentSubscription:
        return await self._subscriptions.of(query.actor.id)

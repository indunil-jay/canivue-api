from app.features.billing.application.queries.list_plans.list_plans_query import ListPlansQuery
from app.features.billing.domain.constants import PLANS
from app.features.billing.domain.value_objects.subscription_plan import SubscriptionPlan


class ListPlansQueryHandler:
    async def handle(self, query: ListPlansQuery) -> list[SubscriptionPlan]:
        return sorted(PLANS.values(), key=lambda p: p.price_monthly)

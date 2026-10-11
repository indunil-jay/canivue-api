from fastapi import APIRouter, Depends

from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.dashboard.application.queries.get_dashboard_summary.get_dashboard_summary_query import (
    GetDashboardSummaryQuery,
)
from app.features.dashboard.application.queries.get_dashboard_summary.get_dashboard_summary_query_handler import (
    GetDashboardSummaryQueryHandler,
)
from app.features.dashboard.application.queries.get_health_insights.get_health_insights_query import (
    GetHealthInsightsQuery,
)
from app.features.dashboard.application.queries.get_health_insights.get_health_insights_query_handler import (
    GetHealthInsightsQueryHandler,
)
from app.features.dashboard.application.queries.get_health_timeline.get_health_timeline_query import (
    GetHealthTimelineQuery,
)
from app.features.dashboard.application.queries.get_health_timeline.get_health_timeline_query_handler import (
    GetHealthTimelineQueryHandler,
)
from app.features.dashboard.presentation.dependencies import (
    get_dashboard_summary_query_handler,
    get_health_insights_query_handler,
    get_health_timeline_query_handler,
)
from app.features.dashboard.presentation.responses.dashboard_summary_response import (
    DashboardSummaryResponse,
)
from app.features.dashboard.presentation.responses.health_insight_response import (
    HealthInsightResponse,
)
from app.features.dashboard.presentation.responses.health_timeline_event_response import (
    HealthTimelineEventResponse,
)
from app.shared.actor import Actor

router = APIRouter()


@router.get(
    "/{dog_id}/dashboard",
    response_model=APIResponse[DashboardSummaryResponse],
    summary="Everything the home screen shows for one Dog",
)
async def get_dashboard(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetDashboardSummaryQueryHandler = Depends(get_dashboard_summary_query_handler),
) -> APIResponse[DashboardSummaryResponse]:
    summary = await handler.handle(GetDashboardSummaryQuery(actor=actor, dog_id=dog_id))
    return APIResponse(
        message="Dashboard retrieved successfully",
        data=DashboardSummaryResponse.model_validate(summary),
    )


@router.get(
    "/{dog_id}/timeline",
    response_model=APIResponse[list[HealthTimelineEventResponse]],
    summary="A Dog's unified health timeline, newest first",
)
async def get_timeline(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetHealthTimelineQueryHandler = Depends(get_health_timeline_query_handler),
) -> APIResponse[list[HealthTimelineEventResponse]]:
    events = await handler.handle(GetHealthTimelineQuery(actor=actor, dog_id=dog_id))
    return APIResponse(
        message="Timeline retrieved successfully",
        data=[HealthTimelineEventResponse.model_validate(e) for e in events],
    )


@router.get(
    "/{dog_id}/insights",
    response_model=APIResponse[list[HealthInsightResponse]],
    summary="Long-term trend statements for a Dog",
    description="One statement per metric that has readings in both of the last two 30-day "
    "periods. Empty until there is that much history.",
)
async def get_insights(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetHealthInsightsQueryHandler = Depends(get_health_insights_query_handler),
) -> APIResponse[list[HealthInsightResponse]]:
    insights = await handler.handle(GetHealthInsightsQuery(actor=actor, dog_id=dog_id))
    return APIResponse(
        message="Insights retrieved successfully",
        data=[HealthInsightResponse.model_validate(i) for i in insights],
    )

def health_score(
    latest_risk_percent: float | None, abnormal_vitals: int, has_data: bool
) -> int | None:
    """100 minus half the latest predicted risk and 5 per vital currently off baseline.

    None when there is nothing to judge by: no readings and no prediction.
    """
    if not has_data:
        return None
    score = 100 - (latest_risk_percent or 0) * 0.5 - 5 * abnormal_vitals
    return max(0, min(100, round(score)))

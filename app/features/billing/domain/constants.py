from datetime import timedelta

from app.features.billing.domain.value_objects.subscription_plan import SubscriptionPlan

UNLIMITED = -1

BILLING_PERIOD = timedelta(days=30)

FREE_PLAN_ID = "free"

PLANS: dict[str, SubscriptionPlan] = {
    p.id: p
    for p in (
        SubscriptionPlan(
            "free", "Free", 0.0,
            ("1 dog profile", "5 AI analyses / month", "Community access"),
            max_dogs=1, ai_analyses_per_month=5, max_devices=1, vet_consultations_per_month=1,
        ),
        SubscriptionPlan(
            "premium", "Premium", 12.99,
            (
                "Up to 3 dogs", "Unlimited AI analyses", "2 smart collar devices",
                "2 vet consultations / month", "Priority support",
            ),
            max_dogs=3, ai_analyses_per_month=UNLIMITED, max_devices=2,
            vet_consultations_per_month=2,
        ),
        SubscriptionPlan(
            "pro", "Pro", 24.99,
            (
                "Unlimited dogs", "Unlimited AI analyses", "Unlimited devices",
                "Unlimited vet consultations", "Dedicated care coordinator",
            ),
            max_dogs=UNLIMITED, ai_analyses_per_month=UNLIMITED, max_devices=UNLIMITED,
            vet_consultations_per_month=UNLIMITED,
        ),
    )
}  # fmt: skip

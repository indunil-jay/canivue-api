from datetime import datetime, timedelta, timezone

import pytest

from app.features.billing.domain.entities import PaymentGatewayProtocol
from app.features.billing.presentation.router import get_payment_gateway
from tests.helpers import book_appointment, create_dog, owner_headers, verified_vet

BILLING = "/api/v1/billing"


class DecliningGateway(PaymentGatewayProtocol):
    async def charge(self, user_id: int, amount: float, description: str) -> bool:
        return False


async def _current(client, headers) -> dict:
    resp = await client.get(f"{BILLING}/subscription", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _change(client, headers, plan_id):
    return await client.put(f"{BILLING}/subscription", headers=headers, json={"plan_id": plan_id})


def _usage(current: dict) -> dict[str, tuple[int, int]]:
    return {u["label"]: (u["used"], u["limit"]) for u in current["usage"]}


async def test_plans_are_listed_cheapest_first(client):
    headers = await owner_headers(client)

    plans = (await client.get(f"{BILLING}/plans", headers=headers)).json()["data"]

    assert [(p["id"], p["name"], p["price_monthly"]) for p in plans] == [
        ("free", "Free", 0.0),
        ("premium", "Premium", 12.99),
        ("pro", "Pro", 24.99),
    ]
    assert "Unlimited dogs" in plans[2]["features"]


async def test_a_new_user_is_on_the_free_plan(client):
    headers = await owner_headers(client)

    current = await _current(client, headers)

    assert current["plan_id"] == "free"
    assert current["renews_at"] is None
    assert current["invoices"] == []
    assert _usage(current) == {
        "Dog Profiles": (0, 1),
        "AI Analyses": (0, 5),
        "Connected Devices": (0, 1),
        "Vet Consultations": (0, 1),
    }


async def test_upgrading_charges_a_month_and_records_a_paid_invoice(client):
    headers = await owner_headers(client)

    resp = await _change(client, headers, "premium")

    assert resp.status_code == 200
    current = resp.json()["data"]
    assert current["plan_id"] == "premium"
    renews = datetime.fromisoformat(current["renews_at"])
    assert timedelta(days=29) < renews - datetime.now(timezone.utc) <= timedelta(days=30)
    assert [(i["amount"], i["status"]) for i in current["invoices"]] == [(12.99, "paid")]
    assert _usage(current)["AI Analyses"] == (0, -1)
    assert _usage(current)["Dog Profiles"] == (0, 3)
    assert (await _current(client, headers))["plan_id"] == "premium"


async def test_choosing_the_current_plan_changes_nothing(client):
    headers = await owner_headers(client)
    await _change(client, headers, "premium")

    again = (await _change(client, headers, "premium")).json()["data"]

    assert len(again["invoices"]) == 1


async def test_invoices_are_newest_first_across_plan_changes(client):
    headers = await owner_headers(client)
    await _change(client, headers, "premium")

    current = (await _change(client, headers, "pro")).json()["data"]

    assert [i["amount"] for i in current["invoices"]] == [24.99, 12.99]


async def test_downgrading_to_free_creates_no_invoice_and_stops_renewal(client):
    headers = await owner_headers(client)
    await _change(client, headers, "pro")

    current = (await _change(client, headers, "free")).json()["data"]

    assert current["plan_id"] == "free"
    assert current["renews_at"] is None
    assert len(current["invoices"]) == 1


async def test_a_declined_payment_leaves_the_plan_unchanged(client):
    headers = await owner_headers(client)
    # The app instance lives on the transport, which is how the test client reaches it.
    client._transport.app.dependency_overrides[get_payment_gateway] = lambda: DecliningGateway()

    resp = await _change(client, headers, "premium")

    assert resp.status_code == 402
    current = await _current(client, headers)
    assert current["plan_id"] == "free"
    assert current["invoices"] == []


async def test_unknown_plans_are_rejected(client):
    headers = await owner_headers(client)

    assert (await _change(client, headers, "platinum")).status_code == 404


async def test_usage_is_counted_from_real_data(client, db_session):
    owner = await owner_headers(client)
    dog = await create_dog(client, owner)
    await create_dog(client, owner, name="Luna")
    base = f"/api/v1/dogs/{dog['id']}"
    await client.post(f"{base}/device/pair", headers=owner)
    for _ in range(2):
        await client.post(
            f"{base}/health-checks", headers=owner, data={"symptom_text": "He is limping badly"}
        )
    vet, vet_id = await verified_vet(client, db_session)
    scene = {"owner": owner, "dog": dog, "vet_id": vet_id}
    done = await book_appointment(client, scene)
    for action in ("confirm", "complete"):
        await client.post(f"/api/v1/appointments/{done['id']}/{action}", headers=vet)

    usage = _usage(await _current(client, owner))

    assert usage["Dog Profiles"] == (2, 1)
    assert usage["AI Analyses"] == (2, 5)
    assert usage["Connected Devices"] == (1, 1)
    # The completed appointment is next week, inside the current period.
    assert usage["Vet Consultations"] == (1, 1)


async def test_usage_is_per_user(client):
    alice = await owner_headers(client, "alice@example.com")
    bob = await owner_headers(client, "bob@example.com")
    await create_dog(client, alice)
    await _change(client, alice, "pro")

    bobs = await _current(client, bob)

    assert bobs["plan_id"] == "free"
    assert bobs["invoices"] == []
    assert _usage(bobs)["Dog Profiles"] == (0, 1)


async def test_changing_plan_sends_a_billing_notification(client):
    headers = await owner_headers(client)

    await _change(client, headers, "premium")

    inbox = (await client.get("/api/v1/notifications", headers=headers)).json()["data"]
    assert inbox["items"][0]["type"] == "billing"
    assert inbox["items"][0]["title"] == "You're now on the Premium plan"
    assert "$12.99" in inbox["items"][0]["message"]


@pytest.mark.parametrize("path", ["plans", "subscription"])
async def test_billing_requires_authentication(client, path):
    assert (await client.get(f"{BILLING}/{path}")).status_code == 401

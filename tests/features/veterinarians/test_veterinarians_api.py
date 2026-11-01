from datetime import datetime, timezone

from app.features.auth.infrastructure.persistence.seed import seed_rbac_catalog
from tests.helpers import admin_headers, owner_headers, verified_vet, vet_headers

VETS = "/api/v1/veterinarians"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TODAY = WEEKDAYS[datetime.now(timezone.utc).weekday()]


async def _search(client, headers, **params) -> list[dict]:
    resp = await client.get(VETS, headers=headers, params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def test_registering_as_a_veterinarian_creates_an_unverified_profile(client):
    headers = await vet_headers(client, "vet@example.com", full_name="Dr. Sarah Jenkins")

    me = (await client.get(f"{VETS}/me", headers=headers)).json()["data"]

    assert me["name"] == "Dr. Sarah Jenkins"
    assert me["initials"] == "SJ"
    assert me["verified"] is False
    assert (await client.get("/api/v1/auth/me", headers=headers)).json()["data"]["role"] == "VET"


async def test_nobody_can_self_register_as_an_administrator(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "sneaky@example.com", "password": "Password123!", "role": "ADMIN"},
    )

    assert resp.status_code == 422


async def test_owners_have_no_professional_profile(client):
    headers = await owner_headers(client)

    assert (await client.get(f"{VETS}/me", headers=headers)).status_code == 403


async def test_unverified_veterinarians_are_hidden_from_owners(client):
    vet = await vet_headers(client, "vet@example.com", full_name="Dr. Hidden")
    owner = await owner_headers(client)
    vet_id = (await client.get(f"{VETS}/me", headers=vet)).json()["data"]["id"]

    assert await _search(client, owner) == []
    assert (await client.get(f"{VETS}/{vet_id}", headers=owner)).status_code == 404
    assert (await client.get(f"{VETS}/{vet_id}", headers=vet)).status_code == 200


async def test_admin_verifies_a_pending_veterinarian(client, db_session):
    vet = await vet_headers(client, "vet@example.com", full_name="Dr. Sarah Jenkins")
    owner = await owner_headers(client)
    admin = await admin_headers(client, db_session)
    pending = (await client.get(f"{VETS}/pending", headers=admin)).json()["data"]
    assert [p["name"] for p in pending] == ["Dr. Sarah Jenkins"]

    resp = await client.post(f"{VETS}/{pending[0]['id']}/verify", headers=admin)

    assert resp.status_code == 200
    assert [v["name"] for v in await _search(client, owner)] == ["Dr. Sarah Jenkins"]
    assert (await client.get(f"{VETS}/pending", headers=admin)).json()["data"] == []
    assert (await client.get(f"{VETS}/me", headers=vet)).json()["data"]["verified"] is True


async def test_only_admins_can_verify(client):
    vet = await vet_headers(client, "vet@example.com")
    vet_id = (await client.get(f"{VETS}/me", headers=vet)).json()["data"]["id"]

    assert (await client.post(f"{VETS}/{vet_id}/verify", headers=vet)).status_code == 403
    assert (await client.get(f"{VETS}/pending", headers=vet)).status_code == 403


async def test_veterinarian_edits_their_professional_profile(client, db_session):
    vet, vet_id = await verified_vet(client, db_session)
    owner = await owner_headers(client)

    resp = await client.patch(
        f"{VETS}/me",
        headers=vet,
        json={
            "specialty": "Dermatology",
            "specialties": ["Dermatology", "Allergy"],
            "experience_years": 9,
            "consultation_fee_usd": 45.0,
            "languages": ["English", "Sinhala"],
            "consultation_types": ["video", "inPerson"],
            "bio": "Skin specialist.",
            "clinics": ["Bay Area Vet"],
            "qualifications": ["DVM"],
        },
    )

    assert resp.status_code == 200
    seen = (await client.get(f"{VETS}/{vet_id}", headers=owner)).json()["data"]
    assert seen["specialty"] == "Dermatology"
    assert seen["consultation_fee_usd"] == 45.0
    assert seen["consultation_types"] == ["video", "inPerson"]
    assert seen["clinics"] == ["Bay Area Vet"]
    assert seen["rating"] == 0.0
    assert seen["review_count"] == 0


async def test_search_filters_by_query_specialty_and_consultation_type(client, db_session):
    owner = await owner_headers(client)
    await verified_vet(
        client,
        db_session,
        "skin@example.com",
        "Dr. Amy Skin",
        specialty="Dermatology",
        consultation_types=["video"],
    )
    await verified_vet(
        client,
        db_session,
        "bones@example.com",
        "Dr. Bob Bones",
        specialty="Orthopedics",
        consultation_types=["inPerson"],
    )

    assert len(await _search(client, owner)) == 2
    assert [v["name"] for v in await _search(client, owner, q="amy")] == ["Dr. Amy Skin"]
    assert [v["name"] for v in await _search(client, owner, q="ortho")] == ["Dr. Bob Bones"]
    by_specialty = await _search(client, owner, specialty="Dermatology")
    assert [v["name"] for v in by_specialty] == ["Dr. Amy Skin"]
    by_type = await _search(client, owner, consultation_type="inPerson")
    assert [v["name"] for v in by_type] == ["Dr. Bob Bones"]
    assert await _search(client, owner, q="nobody") == []


async def test_availability_defaults_to_weekdays(client):
    vet = await vet_headers(client, "vet@example.com")

    availability = (await client.get(f"{VETS}/me/availability", headers=vet)).json()["data"]

    assert list(availability) == WEEKDAYS
    assert availability["Monday"] is True
    assert availability["Friday"] is True
    assert availability["Saturday"] is False
    assert availability["Sunday"] is False


async def test_veterinarian_changes_one_day(client):
    vet = await vet_headers(client, "vet@example.com")

    resp = await client.put(
        f"{VETS}/me/availability/Saturday", headers=vet, json={"available": True}
    )

    assert resp.status_code == 200
    saved = (await client.get(f"{VETS}/me/availability", headers=vet)).json()["data"]
    assert saved["Saturday"] is True
    assert saved["Sunday"] is False
    assert saved["Monday"] is True


async def test_unknown_weekday_is_rejected(client):
    vet = await vet_headers(client, "vet@example.com")

    resp = await client.put(f"{VETS}/me/availability/Funday", headers=vet, json={"available": True})

    assert resp.status_code == 422


async def test_discovery_reflects_availability_today(client, db_session):
    owner = await owner_headers(client)
    vet, vet_id = await verified_vet(client, db_session)
    await client.put(f"{VETS}/me/availability/{TODAY}", headers=vet, json={"available": False})

    assert (await _search(client, owner))[0]["available_today"] is False
    assert await _search(client, owner, available_today=True) == []

    await client.put(f"{VETS}/me/availability/{TODAY}", headers=vet, json={"available": True})

    assert [v["id"] for v in await _search(client, owner, available_today=True)] == [vet_id]


async def test_staff_created_veterinarians_are_verified(client, db_session):
    await seed_rbac_catalog(db_session)
    owner = await owner_headers(client)
    admin = await admin_headers(client, db_session)

    resp = await client.post(
        "/api/v1/auth/staff",
        headers=admin,
        json={
            "email": "staffvet@example.com",
            "password": "Password123!",
            "role": "VET",
            "full_name": "Dr. Staff",
        },
    )

    assert resp.status_code == 201
    assert [v["name"] for v in await _search(client, owner)] == ["Dr. Staff"]

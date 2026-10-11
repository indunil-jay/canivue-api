from datetime import date, timedelta

from tests.helpers import admin_headers, owner_headers

DOGS = "/api/v1/dogs"


def buddy(**overrides) -> dict:
    return {
        "name": "Buddy",
        "breed": "Golden Retriever",
        "birth_date": "2023-06-12",
        "gender": "Male",
        "weight_kg": 28.5,
        **overrides,
    }


async def _create(client, headers, **overrides) -> dict:
    resp = await client.post(DOGS, headers=headers, json=buddy(**overrides))
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def test_owner_registers_a_dog_with_its_full_profile(client):
    headers = await owner_headers(client)

    dog = await _create(
        client,
        headers,
        color="Golden Honey",
        microchip_id="985141002348123",
        is_neutered=True,
        allergies=["Wheat (mild)"],
        existing_conditions=["Mild hip dysplasia"],
        vaccinations=[
            {"name": "Rabies", "date_given": "2025-06-01", "next_due_date": "2026-06-01"}
        ],
        medications=[{"name": "Joint Support Chews", "dosage": "1 chew", "frequency": "Daily"}],
        insurance={
            "provider": "PetGuard Plus",
            "policy_number": "PG-88213",
            "expiry_date": "2026-12-31",
        },
    )

    fetched = (await client.get(f"{DOGS}/{dog['id']}", headers=headers)).json()["data"]
    assert fetched["name"] == "Buddy"
    assert fetched["gender"] == "Male"
    assert fetched["allergies"] == ["Wheat (mild)"]
    assert fetched["vaccinations"] == [
        {"name": "Rabies", "date_given": "2025-06-01", "next_due_date": "2026-06-01"}
    ]
    assert fetched["medications"][0]["frequency"] == "Daily"
    assert fetched["insurance"]["policy_number"] == "PG-88213"


async def test_age_is_computed_from_the_birth_date(client):
    headers = await owner_headers(client)
    today = date.today()
    born = date(today.year - 2, today.month, 1) - timedelta(days=62)

    dog = await _create(client, headers, birth_date=born.isoformat())

    assert dog["age_years"] == 2
    assert dog["age_months"] in (2, 3)


async def test_owner_lists_only_their_own_dogs(client):
    alice = await owner_headers(client, "alice@example.com")
    bob = await owner_headers(client, "bob@example.com")
    await _create(client, alice, name="Buddy")
    await _create(client, alice, name="Luna")
    await _create(client, bob, name="Charlie")

    names = [d["name"] for d in (await client.get(DOGS, headers=alice)).json()["data"]]

    assert names == ["Buddy", "Luna"]


async def test_another_owners_dog_is_not_found(client):
    alice = await owner_headers(client, "alice@example.com")
    bob = await owner_headers(client, "bob@example.com")
    dog = await _create(client, alice)
    url = f"{DOGS}/{dog['id']}"

    assert (await client.get(url, headers=bob)).status_code == 404
    assert (await client.patch(url, headers=bob, json={"name": "Mine"})).status_code == 404
    assert (await client.delete(url, headers=bob)).status_code == 404
    assert (await client.get(url, headers=alice)).json()["data"]["name"] == "Buddy"


async def test_owner_updates_part_of_a_dog_profile(client):
    headers = await owner_headers(client)
    dog = await _create(client, headers, allergies=["Chicken"])

    resp = await client.patch(
        f"{DOGS}/{dog['id']}", headers=headers, json={"weight_kg": 30.1, "special_notes": "Swims"}
    )

    updated = resp.json()["data"]
    assert updated["weight_kg"] == 30.1
    assert updated["special_notes"] == "Swims"
    assert updated["allergies"] == ["Chicken"]
    assert updated["name"] == "Buddy"


async def test_insurance_can_be_cleared(client):
    headers = await owner_headers(client)
    dog = await _create(
        client,
        headers,
        insurance={"provider": "P", "policy_number": "1", "expiry_date": "2027-01-01"},
    )

    resp = await client.patch(f"{DOGS}/{dog['id']}", headers=headers, json={"insurance": None})

    assert resp.json()["data"]["insurance"] is None


async def test_removed_dog_disappears(client):
    headers = await owner_headers(client)
    dog = await _create(client, headers)

    assert (await client.delete(f"{DOGS}/{dog['id']}", headers=headers)).status_code == 200

    assert (await client.get(f"{DOGS}/{dog['id']}", headers=headers)).status_code == 404
    assert (await client.get(DOGS, headers=headers)).json()["data"] == []


async def test_invalid_dogs_are_rejected(client):
    headers = await owner_headers(client)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    assert (await client.post(DOGS, headers=headers, json=buddy(weight_kg=0))).status_code == 422
    assert (await client.post(DOGS, headers=headers, json=buddy(gender="Robot"))).status_code == 422
    future = await client.post(DOGS, headers=headers, json=buddy(birth_date=tomorrow))
    assert future.status_code == 422


async def test_dogs_require_authentication(client):
    assert (await client.get(DOGS)).status_code == 401
    assert (await client.post(DOGS, json=buddy())).status_code == 401


async def test_admin_can_read_any_dog(client, db_session):
    owner = await owner_headers(client)
    dog = await _create(client, owner)
    admin = await admin_headers(client, db_session)

    assert (await client.get(f"{DOGS}/{dog['id']}", headers=admin)).status_code == 200

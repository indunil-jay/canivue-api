import pytest

from tests.helpers import book_appointment, create_dog, next_weekday, owner_headers, verified_vet

API = "/api/v1"


@pytest.fixture
async def scene(client, db_session):
    owner = await owner_headers(client, full_name="Alex Taylor")
    dog = await create_dog(client, owner)
    vet, vet_id = await verified_vet(client, db_session)
    return {"owner": owner, "dog": dog, "vet": vet, "vet_id": vet_id}


async def _completed(client, scene, hour=10) -> dict:
    appointment = await book_appointment(client, scene, when=next_weekday(0, hour=hour))
    for action in ("confirm", "complete"):
        await client.post(f"{API}/appointments/{appointment['id']}/{action}", headers=scene["vet"])
    return appointment


async def _review(client, headers, appointment_id, rating=5, comment="Very thorough."):
    return await client.post(
        f"{API}/reviews",
        headers=headers,
        json={"appointment_id": appointment_id, "rating": rating, "comment": comment},
    )


async def _vet(client, scene) -> dict:
    resp = await client.get(f"{API}/veterinarians/{scene['vet_id']}", headers=scene["owner"])
    return resp.json()["data"]


async def test_owner_reviews_a_completed_appointment(client, scene):
    appointment = await _completed(client, scene)

    resp = await _review(client, scene["owner"], appointment["id"], 4, "Ran a bit long.")

    assert resp.status_code == 201
    assert resp.json()["data"]["owner_name"] == "Alex Taylor"
    assert resp.json()["data"]["rating"] == 4
    listed = await client.get(
        f"{API}/veterinarians/{scene['vet_id']}/reviews", headers=scene["owner"]
    )
    assert [r["comment"] for r in listed.json()["data"]] == ["Ran a bit long."]


async def test_an_appointment_that_is_not_completed_cannot_be_reviewed(client, scene):
    appointment = await book_appointment(client, scene)

    assert (await _review(client, scene["owner"], appointment["id"])).status_code == 409


async def test_an_appointment_can_be_reviewed_only_once(client, scene):
    appointment = await _completed(client, scene)
    await _review(client, scene["owner"], appointment["id"])

    assert (await _review(client, scene["owner"], appointment["id"])).status_code == 409


async def test_only_the_owner_of_the_appointment_can_review_it(client, scene):
    appointment = await _completed(client, scene)
    stranger = await owner_headers(client, "stranger@example.com")

    assert (await _review(client, stranger, appointment["id"])).status_code == 404
    assert (await _review(client, scene["vet"], appointment["id"])).status_code == 404


@pytest.mark.parametrize("rating", [0, 6])
async def test_ratings_outside_one_to_five_are_rejected(client, scene, rating):
    appointment = await _completed(client, scene)

    assert (await _review(client, scene["owner"], appointment["id"], rating)).status_code == 422


async def test_discovery_figures_come_from_reviews_and_completed_appointments(client, scene):
    before = await _vet(client, scene)
    first = await _completed(client, scene, hour=9)
    second = await _completed(client, scene, hour=11)
    await book_appointment(client, scene, when=next_weekday(0, hour=15))
    await _review(client, scene["owner"], first["id"], 5)
    await _review(client, scene["owner"], second["id"], 4)

    after = await _vet(client, scene)

    assert (before["rating"], before["review_count"], before["consultation_count"]) == (0.0, 0, 0)
    assert (after["rating"], after["review_count"], after["consultation_count"]) == (4.5, 2, 2)
    assert after["follow_up_rate_percent"] == 100


async def test_veterinarian_sees_their_reputation(client, scene):
    first = await _completed(client, scene, hour=9)
    await _completed(client, scene, hour=11)
    other_owner = await owner_headers(client, "other@example.com", full_name="Priya M")
    other_dog = await create_dog(client, other_owner, name="Luna")
    once = await _completed(client, {**scene, "owner": other_owner, "dog": other_dog}, hour=14)
    await _review(client, scene["owner"], first["id"], 5, "Great with anxious dogs.")
    await _review(client, other_owner, once["id"], 3, "Fine.")

    resp = await client.get(f"{API}/veterinarians/me/reputation", headers=scene["vet"])

    reputation = resp.json()["data"]
    assert resp.status_code == 200
    assert reputation["average_rating"] == 4.0
    assert reputation["total_consultations"] == 3
    # One of the two owners came back.
    assert reputation["repeat_consultation_percent"] == 50
    assert reputation["recommendations_accepted_percent"] == 0
    assert sorted(r["owner_name"] for r in reputation["reviews"]) == ["Alex Taylor", "Priya M"]


async def test_reputation_is_for_veterinarians_only(client, scene):
    resp = await client.get(f"{API}/veterinarians/me/reputation", headers=scene["owner"])

    assert resp.status_code == 403


async def test_better_rated_veterinarians_are_listed_first(client, scene, db_session):
    _, other_id = await verified_vet(client, db_session, "aaa@example.com", "Dr. Aaron First")
    appointment = await _completed(client, scene)
    await _review(client, scene["owner"], appointment["id"], 5)

    listed = (await client.get(f"{API}/veterinarians", headers=scene["owner"])).json()["data"]

    assert [v["id"] for v in listed] == [scene["vet_id"], other_id]

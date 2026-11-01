from datetime import datetime, timedelta, timezone

import pytest

from tests.helpers import (
    book_appointment,
    create_dog,
    next_weekday,
    owner_headers,
    verified_vet,
)

DOGS = "/api/v1/dogs"
APPTS = "/api/v1/appointments"
MONDAY, SATURDAY = 0, 5


@pytest.fixture
async def scene(client, db_session):
    """An owner with a Dog, and a verified veterinarian charging 40."""
    owner = await owner_headers(client, full_name="Alex Taylor")
    dog = await create_dog(client, owner)
    vet, vet_id = await verified_vet(client, db_session, consultation_types=["video", "chat"])
    return {"owner": owner, "dog": dog, "vet": vet, "vet_id": vet_id}


async def _book_raw(client, scene, **overrides):
    payload = {
        "vet_id": scene["vet_id"],
        "date_time": next_weekday(MONDAY).isoformat(),
        "consultation_type": "video",
        **overrides,
    }
    return await client.post(
        f"{DOGS}/{scene['dog']['id']}/appointments", headers=scene["owner"], json=payload
    )


async def _act(client, headers, appointment_id, action):
    return await client.post(f"{APPTS}/{appointment_id}/{action}", headers=headers)


async def test_owner_books_an_appointment_that_starts_as_requested(client, scene):
    resp = await _book_raw(client, scene, notes="Limping since Sunday")

    assert resp.status_code == 201
    appointment = resp.json()["data"]
    assert appointment["status"] == "requested"
    assert appointment["dog_name"] == "Buddy"
    assert appointment["vet_name"] == "Dr. Sarah Jenkins"
    assert appointment["owner_name"] == "Alex Taylor"
    assert appointment["consultation_type"] == "video"
    assert appointment["notes"] == "Limping since Sunday"


async def test_fee_comes_from_the_veterinarian_not_the_client(client, scene):
    resp = await _book_raw(client, scene, fee_usd=0.01)

    assert resp.json()["data"]["fee_usd"] == 40.0


async def test_booking_in_the_past_is_rejected(client, scene):
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)

    resp = await _book_raw(client, scene, date_time=yesterday.isoformat())

    assert resp.status_code == 422
    assert "future" in resp.json()["error"]["message"]


async def test_booking_on_an_unavailable_day_is_rejected(client, scene):
    resp = await _book_raw(client, scene, date_time=next_weekday(SATURDAY).isoformat())

    assert resp.status_code == 422
    assert "does not take appointments" in resp.json()["error"]["message"]


async def test_booking_an_unsupported_consultation_type_is_rejected(client, scene):
    resp = await _book_raw(client, scene, consultation_type="inPerson")

    assert resp.status_code == 422


async def test_booking_a_taken_slot_is_rejected(client, scene):
    assert (await _book_raw(client, scene)).status_code == 201
    other_owner = await owner_headers(client, "other@example.com")
    other_dog = await create_dog(client, other_owner, name="Luna")

    resp = await client.post(
        f"{DOGS}/{other_dog['id']}/appointments",
        headers=other_owner,
        json={
            "vet_id": scene["vet_id"],
            "date_time": next_weekday(MONDAY).isoformat(),
            "consultation_type": "video",
        },
    )

    assert resp.status_code == 409


async def test_a_cancelled_slot_can_be_booked_again(client, scene):
    first = (await _book_raw(client, scene)).json()["data"]
    await _act(client, scene["owner"], first["id"], "cancel")

    assert (await _book_raw(client, scene)).status_code == 201


async def test_booking_with_an_unverified_veterinarian_is_rejected(client, scene):
    from tests.helpers import vet_headers

    unverified = await vet_headers(client, "new@example.com")
    vet_id = (await client.get("/api/v1/veterinarians/me", headers=unverified)).json()["data"]["id"]

    assert (await _book_raw(client, scene, vet_id=vet_id)).status_code == 404


async def test_owner_cannot_book_for_someone_elses_dog(client, scene):
    stranger = await owner_headers(client, "stranger@example.com")

    resp = await client.post(
        f"{DOGS}/{scene['dog']['id']}/appointments",
        headers=stranger,
        json={
            "vet_id": scene["vet_id"],
            "date_time": next_weekday(MONDAY).isoformat(),
            "consultation_type": "video",
        },
    )

    assert resp.status_code == 404


async def test_owner_lists_a_dogs_appointments_in_time_order(client, scene):
    later = await book_appointment(client, scene, when=next_weekday(MONDAY, hour=15))
    earlier = await book_appointment(client, scene, when=next_weekday(MONDAY, hour=9))

    resp = await client.get(f"{DOGS}/{scene['dog']['id']}/appointments", headers=scene["owner"])

    assert [a["id"] for a in resp.json()["data"]] == [earlier["id"], later["id"]]


async def test_veterinarian_lists_appointments_booked_with_them(client, scene, db_session):
    mine = await book_appointment(client, scene)
    other_vet, _ = await verified_vet(client, db_session, "other-vet@example.com", "Dr. Other")

    listed = (await client.get(APPTS, headers=scene["vet"])).json()["data"]

    assert [a["id"] for a in listed] == [mine["id"]]
    assert (await client.get(APPTS, headers=other_vet)).json()["data"] == []


async def test_my_appointments_can_be_filtered_by_status(client, scene):
    first = await book_appointment(client, scene, when=next_weekday(MONDAY, hour=9))
    await book_appointment(client, scene, when=next_weekday(MONDAY, hour=11))
    await _act(client, scene["vet"], first["id"], "confirm")

    confirmed = await client.get(APPTS, headers=scene["owner"], params={"status": "confirmed"})

    assert [a["id"] for a in confirmed.json()["data"]] == [first["id"]]


async def test_veterinarian_takes_an_appointment_through_to_completion(client, scene):
    appointment = await book_appointment(client, scene)
    statuses = []

    for action in ("confirm", "start", "complete"):
        resp = await _act(client, scene["vet"], appointment["id"], action)
        assert resp.status_code == 200
        statuses.append(resp.json()["data"]["status"])

    assert statuses == ["confirmed", "inProgress", "completed"]


async def test_veterinarian_can_mark_a_confirmed_appointment_no_show(client, scene):
    appointment = await book_appointment(client, scene)
    await _act(client, scene["vet"], appointment["id"], "confirm")

    resp = await _act(client, scene["vet"], appointment["id"], "no-show")

    assert resp.json()["data"]["status"] == "noShow"


@pytest.mark.parametrize("terminal", ["complete", "cancel", "no-show"])
async def test_terminal_appointments_cannot_change(client, scene, terminal):
    appointment = await book_appointment(client, scene)
    await _act(client, scene["vet"], appointment["id"], "confirm")
    assert (await _act(client, scene["vet"], appointment["id"], terminal)).status_code == 200

    for action in ("confirm", "start", "complete", "cancel", "no-show"):
        assert (await _act(client, scene["vet"], appointment["id"], action)).status_code == 409


async def test_a_requested_appointment_cannot_be_completed_directly(client, scene):
    appointment = await book_appointment(client, scene)

    assert (await _act(client, scene["vet"], appointment["id"], "complete")).status_code == 409


async def test_owner_can_cancel_but_not_confirm_or_complete(client, scene):
    appointment = await book_appointment(client, scene)

    assert (await _act(client, scene["owner"], appointment["id"], "confirm")).status_code == 409
    assert (await _act(client, scene["owner"], appointment["id"], "complete")).status_code == 409
    cancelled = await _act(client, scene["owner"], appointment["id"], "cancel")
    assert cancelled.json()["data"]["status"] == "cancelled"


async def test_strangers_cannot_see_or_change_an_appointment(client, scene, db_session):
    appointment = await book_appointment(client, scene)
    stranger = await owner_headers(client, "stranger@example.com")
    other_vet, _ = await verified_vet(client, db_session, "other-vet@example.com", "Dr. Other")

    for headers in (stranger, other_vet):
        assert (
            await client.get(f"{APPTS}/{appointment['id']}", headers=headers)
        ).status_code == 404
        assert (await _act(client, headers, appointment["id"], "cancel")).status_code == 404


async def test_a_dog_becomes_readable_to_its_veterinarian_once_booked(client, scene, db_session):
    dog_url = f"{DOGS}/{scene['dog']['id']}"
    other_vet, _ = await verified_vet(client, db_session, "other-vet@example.com", "Dr. Other")
    assert (await client.get(dog_url, headers=scene["vet"])).status_code == 404

    appointment = await book_appointment(client, scene)

    assert (await client.get(dog_url, headers=scene["vet"])).json()["data"]["name"] == "Buddy"
    assert (await client.get(dog_url, headers=other_vet)).status_code == 404
    assert (
        await client.patch(dog_url, headers=scene["vet"], json={"name": "Hacked"})
    ).status_code == 404

    await _act(client, scene["owner"], appointment["id"], "cancel")

    assert (await client.get(dog_url, headers=scene["vet"])).status_code == 404


async def test_owner_can_stop_sharing_their_dogs_with_veterinarians(client, scene):
    dog_url = f"{DOGS}/{scene['dog']['id']}"
    await book_appointment(client, scene)
    assert (await client.get(dog_url, headers=scene["vet"])).status_code == 200

    await client.patch(
        "/api/v1/auth/me/privacy", headers=scene["owner"], json={"share_with_vet": False}
    )

    assert (await client.get(dog_url, headers=scene["vet"])).status_code == 404
    assert (await client.get(f"{dog_url}/records", headers=scene["vet"])).status_code == 404
    assert (await client.get(dog_url, headers=scene["owner"])).status_code == 200

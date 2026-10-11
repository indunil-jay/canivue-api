import pytest

from tests.helpers import book_appointment, create_dog, owner_headers, verified_vet

NOTIFICATIONS = "/api/v1/notifications"
APPTS = "/api/v1/appointments"


@pytest.fixture
async def scene(client, db_session):
    owner = await owner_headers(client, full_name="Alex Taylor")
    dog = await create_dog(client, owner)
    vet, vet_id = await verified_vet(client, db_session)
    return {"owner": owner, "dog": dog, "vet": vet, "vet_id": vet_id}


async def _inbox(client, headers) -> dict:
    resp = await client.get(NOTIFICATIONS, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def test_inbox_starts_empty(client):
    headers = await owner_headers(client)

    assert await _inbox(client, headers) == {"items": [], "unread_count": 0}


async def test_requesting_an_appointment_notifies_the_veterinarian(client, scene):
    await book_appointment(client, scene)

    vet_inbox = await _inbox(client, scene["vet"])

    assert vet_inbox["unread_count"] == 1
    note = vet_inbox["items"][0]
    assert note["type"] == "vetAppointment"
    assert note["title"] == "New appointment request"
    assert "Alex Taylor" in note["message"] and "Buddy" in note["message"]
    assert note["dog_name"] == "Buddy"
    assert note["is_read"] is False
    assert (await _inbox(client, scene["owner"]))["items"] == []


async def test_confirming_notifies_the_owner(client, scene):
    appointment = await book_appointment(client, scene)

    await client.post(f"{APPTS}/{appointment['id']}/confirm", headers=scene["vet"])

    owner_inbox = await _inbox(client, scene["owner"])
    assert [n["title"] for n in owner_inbox["items"]] == ["Appointment confirmed"]
    assert "Dr. Sarah Jenkins" in owner_inbox["items"][0]["message"]


async def test_cancelling_notifies_the_other_party(client, scene):
    by_owner = await book_appointment(client, scene)
    await client.post(f"{APPTS}/{by_owner['id']}/cancel", headers=scene["owner"])
    by_vet = await book_appointment(client, scene)
    await client.post(f"{APPTS}/{by_vet['id']}/cancel", headers=scene["vet"])

    vet_titles = [n["title"] for n in (await _inbox(client, scene["vet"]))["items"]]
    owner_titles = [n["title"] for n in (await _inbox(client, scene["owner"]))["items"]]

    assert vet_titles.count("Appointment cancelled") == 1
    assert owner_titles == ["Appointment cancelled"]


async def test_notifications_are_listed_newest_first(client, scene):
    appointment = await book_appointment(client, scene)
    await client.post(f"{APPTS}/{appointment['id']}/cancel", headers=scene["owner"])

    titles = [n["title"] for n in (await _inbox(client, scene["vet"]))["items"]]

    assert titles == ["Appointment cancelled", "New appointment request"]


async def test_marking_one_notification_read(client, scene):
    appointment = await book_appointment(client, scene)
    await client.post(f"{APPTS}/{appointment['id']}/cancel", headers=scene["owner"])
    newest = (await _inbox(client, scene["vet"]))["items"][0]

    resp = await client.post(f"{NOTIFICATIONS}/{newest['id']}/read", headers=scene["vet"])

    assert resp.json()["data"] == {"unread_count": 1}
    inbox = await _inbox(client, scene["vet"])
    assert [n["is_read"] for n in inbox["items"]] == [True, False]


async def test_marking_all_notifications_read(client, scene):
    appointment = await book_appointment(client, scene)
    await client.post(f"{APPTS}/{appointment['id']}/cancel", headers=scene["owner"])

    resp = await client.post(f"{NOTIFICATIONS}/read-all", headers=scene["vet"])

    assert resp.json()["data"] == {"unread_count": 0}
    assert all(n["is_read"] for n in (await _inbox(client, scene["vet"]))["items"])


async def test_users_cannot_mark_each_others_notifications(client, scene):
    await book_appointment(client, scene)
    note = (await _inbox(client, scene["vet"]))["items"][0]

    resp = await client.post(f"{NOTIFICATIONS}/{note['id']}/read", headers=scene["owner"])

    assert resp.status_code == 404
    assert (await _inbox(client, scene["vet"]))["unread_count"] == 1


async def test_notifications_require_authentication(client):
    assert (await client.get(NOTIFICATIONS)).status_code == 401

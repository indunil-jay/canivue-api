import pytest

from tests.helpers import create_dog, owner_headers, verified_vet, vet_headers

CONVERSATIONS = "/api/v1/conversations"


@pytest.fixture
async def scene(client, db_session):
    owner = await owner_headers(client, full_name="Alex Taylor")
    vet, vet_id = await verified_vet(client, db_session)
    return {"owner": owner, "vet": vet, "vet_id": vet_id}


async def _start(client, headers, vet_id) -> dict:
    resp = await client.post(CONVERSATIONS, headers=headers, json={"vet_id": vet_id})
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _send(client, headers, conversation_id, text, **extra):
    return await client.post(
        f"{CONVERSATIONS}/{conversation_id}/messages", headers=headers, json={"text": text, **extra}
    )


async def _messages(client, headers, conversation_id, **params) -> list[dict]:
    resp = await client.get(
        f"{CONVERSATIONS}/{conversation_id}/messages", headers=headers, params=params
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _list(client, headers) -> list[dict]:
    return (await client.get(CONVERSATIONS, headers=headers)).json()["data"]


async def test_owner_starts_a_conversation_with_a_veterinarian(client, scene):
    conversation = await _start(client, scene["owner"], scene["vet_id"])

    assert conversation["vet_name"] == "Dr. Sarah Jenkins"
    assert conversation["vet_initials"] == "SJ"
    assert conversation["owner_name"] == "Alex Taylor"
    assert conversation["unread_count"] == 0
    assert conversation["last_message_at"] is None


async def test_starting_again_reopens_the_same_conversation(client, scene):
    first = await _start(client, scene["owner"], scene["vet_id"])

    second = await _start(client, scene["owner"], scene["vet_id"])

    assert second["id"] == first["id"]
    assert len(await _list(client, scene["owner"])) == 1


async def test_conversation_cannot_be_started_with_an_unverified_veterinarian(client, scene):
    unverified = await vet_headers(client, "new@example.com")
    vet_id = (await client.get("/api/v1/veterinarians/me", headers=unverified)).json()["data"]["id"]

    resp = await client.post(CONVERSATIONS, headers=scene["owner"], json={"vet_id": vet_id})

    assert resp.status_code == 404


async def test_both_sides_exchange_messages_in_order(client, scene):
    conversation = await _start(client, scene["owner"], scene["vet_id"])
    await _send(client, scene["owner"], conversation["id"], "Buddy is limping")
    await _send(client, scene["vet"], conversation["id"], "Since when?")

    messages = await _messages(client, scene["owner"], conversation["id"])

    assert [(m["sender"], m["text"]) for m in messages] == [
        ("owner", "Buddy is limping"),
        ("vet", "Since when?"),
    ]
    assert all(m["kind"] == "text" for m in messages)


async def test_conversation_list_shows_preview_and_unread_count(client, scene):
    conversation = await _start(client, scene["owner"], scene["vet_id"])
    await _send(client, scene["owner"], conversation["id"], "First")
    await _send(client, scene["owner"], conversation["id"], "Second")

    vet_view = (await _list(client, scene["vet"]))[0]
    owner_view = (await _list(client, scene["owner"]))[0]

    assert vet_view["last_message_preview"] == "Second"
    assert vet_view["last_message_at"] is not None
    assert vet_view["unread_count"] == 2
    assert owner_view["unread_count"] == 0


async def test_reading_a_conversation_clears_the_unread_count(client, scene):
    conversation = await _start(client, scene["owner"], scene["vet_id"])
    await _send(client, scene["owner"], conversation["id"], "Hello")

    await _messages(client, scene["vet"], conversation["id"])

    assert (await _list(client, scene["vet"]))[0]["unread_count"] == 0


async def test_message_status_moves_from_sent_to_delivered_to_read(client, scene):
    conversation = await _start(client, scene["owner"], scene["vet_id"])
    sent = (await _send(client, scene["owner"], conversation["id"], "Hello")).json()["data"]
    assert sent["status"] == "sent"

    await _list(client, scene["vet"])
    delivered = (await _messages(client, scene["owner"], conversation["id"]))[0]["status"]
    await _messages(client, scene["vet"], conversation["id"])
    read = (await _messages(client, scene["owner"], conversation["id"]))[0]["status"]

    assert (delivered, read) == ("delivered", "read")


async def test_polling_returns_only_newer_messages(client, scene):
    conversation = await _start(client, scene["owner"], scene["vet_id"])
    first = (await _send(client, scene["owner"], conversation["id"], "One")).json()["data"]
    await _send(client, scene["vet"], conversation["id"], "Two")

    newer = await _messages(client, scene["owner"], conversation["id"], after=first["timestamp"])

    assert [m["text"] for m in newer] == ["Two"]


async def test_only_the_veterinarian_can_post_a_consultation_summary(client, scene):
    conversation = await _start(client, scene["owner"], scene["vet_id"])

    by_owner = await _send(
        client, scene["owner"], conversation["id"], "Summary", kind="consultationSummary"
    )
    by_vet = await _send(
        client, scene["vet"], conversation["id"], "Rest for a week", kind="consultationSummary"
    )

    assert by_owner.status_code == 403
    assert by_vet.status_code == 201
    assert by_vet.json()["data"]["kind"] == "consultationSummary"


async def test_non_participants_cannot_see_or_post(client, scene, db_session):
    conversation = await _start(client, scene["owner"], scene["vet_id"])
    await _send(client, scene["owner"], conversation["id"], "Private")
    stranger = await owner_headers(client, "stranger@example.com")
    other_vet, _ = await verified_vet(client, db_session, "other-vet@example.com", "Dr. Other")

    for headers in (stranger, other_vet):
        url = f"{CONVERSATIONS}/{conversation['id']}/messages"
        assert (await client.get(url, headers=headers)).status_code == 404
        assert (await _send(client, headers, conversation["id"], "Hi")).status_code == 404
        assert await _list(client, headers) == []


async def test_empty_messages_are_rejected(client, scene):
    conversation = await _start(client, scene["owner"], scene["vet_id"])

    assert (await _send(client, scene["owner"], conversation["id"], "")).status_code == 422


async def test_receiving_a_message_creates_a_notification(client, scene):
    conversation = await _start(client, scene["owner"], scene["vet_id"])

    await _send(client, scene["owner"], conversation["id"], "Buddy is limping")

    inbox = (await client.get("/api/v1/notifications", headers=scene["vet"])).json()["data"]
    assert inbox["items"][0]["type"] == "vetMessage"
    assert inbox["items"][0]["title"] == "New message from Alex Taylor"
    assert inbox["items"][0]["message"] == "Buddy is limping"


async def test_a_conversation_makes_the_owners_dogs_readable_to_that_veterinarian(client, scene):
    dog = await create_dog(client, scene["owner"])
    dog_url = f"/api/v1/dogs/{dog['id']}"
    assert (await client.get(dog_url, headers=scene["vet"])).status_code == 404

    await _start(client, scene["owner"], scene["vet_id"])

    assert (await client.get(dog_url, headers=scene["vet"])).status_code == 200

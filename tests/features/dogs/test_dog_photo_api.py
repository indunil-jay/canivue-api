from app.config import settings
from tests.features.dogs.test_dogs_api import DOGS, _create
from tests.helpers import owner_headers

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32


def _upload(content: bytes, content_type: str = "image/png", name: str = "dog.png") -> dict:
    return {"file": (name, content, content_type)}


async def test_owner_uploads_and_fetches_a_dog_photo(client):
    headers = await owner_headers(client)
    dog = await _create(client, headers)
    url = f"{DOGS}/{dog['id']}/photo"
    assert dog["has_photo"] is False

    resp = await client.put(url, headers=headers, files=_upload(PNG))

    assert resp.status_code == 200
    assert resp.json()["data"]["has_photo"] is True
    photo = await client.get(url, headers=headers)
    assert photo.status_code == 200
    assert photo.content == PNG
    assert photo.headers["content-type"] == "image/png"


async def test_replacing_a_photo_serves_the_new_one(client):
    headers = await owner_headers(client)
    dog = await _create(client, headers)
    url = f"{DOGS}/{dog['id']}/photo"
    await client.put(url, headers=headers, files=_upload(PNG))

    await client.put(url, headers=headers, files=_upload(JPEG, "image/jpeg", "dog.jpg"))

    photo = await client.get(url, headers=headers)
    assert photo.content == JPEG
    assert photo.headers["content-type"] == "image/jpeg"


async def test_dog_without_photo_returns_not_found(client):
    headers = await owner_headers(client)
    dog = await _create(client, headers)

    assert (await client.get(f"{DOGS}/{dog['id']}/photo", headers=headers)).status_code == 404


async def test_owner_removes_a_photo(client):
    headers = await owner_headers(client)
    dog = await _create(client, headers)
    url = f"{DOGS}/{dog['id']}/photo"
    await client.put(url, headers=headers, files=_upload(PNG))

    assert (await client.delete(url, headers=headers)).status_code == 200

    assert (await client.get(url, headers=headers)).status_code == 404


async def test_disallowed_content_types_are_rejected(client):
    headers = await owner_headers(client)
    dog = await _create(client, headers)
    url = f"{DOGS}/{dog['id']}/photo"

    html = await client.put(
        url, headers=headers, files=_upload(b"<html></html>", "text/html", "x.html")
    )
    disguised = await client.put(url, headers=headers, files=_upload(b"<html></html>"))

    assert html.status_code == 415
    assert disguised.status_code == 415


async def test_oversized_photo_is_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 16)
    headers = await owner_headers(client)
    dog = await _create(client, headers)

    resp = await client.put(f"{DOGS}/{dog['id']}/photo", headers=headers, files=_upload(PNG))

    assert resp.status_code == 413


async def test_other_owners_cannot_fetch_or_replace_the_photo(client):
    alice = await owner_headers(client, "alice@example.com")
    bob = await owner_headers(client, "bob@example.com")
    dog = await _create(client, alice)
    url = f"{DOGS}/{dog['id']}/photo"
    await client.put(url, headers=alice, files=_upload(PNG))

    assert (await client.get(url, headers=bob)).status_code == 404
    assert (
        await client.put(url, headers=bob, files=_upload(JPEG, "image/jpeg"))
    ).status_code == 404
    assert (await client.get(url, headers=alice)).content == PNG

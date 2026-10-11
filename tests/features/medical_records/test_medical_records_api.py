import pytest

from tests.helpers import book_appointment, create_dog, owner_headers, verified_vet

PDF = b"%PDF-1.7\n" + b"0" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture
async def scene(client, db_session):
    """An owner whose Dog is a patient of `vet` (through a booked appointment)."""
    owner = await owner_headers(client, full_name="Alex Taylor")
    dog = await create_dog(client, owner)
    vet, vet_id = await verified_vet(client, db_session)
    scene = {"owner": owner, "dog": dog, "vet": vet, "vet_id": vet_id}
    await book_appointment(client, scene)
    scene["url"] = f"/api/v1/dogs/{dog['id']}/records"
    return scene


async def _add(client, headers, url, **overrides):
    payload = {"type": "note", "title": "Observation", "description": "Ate well", **overrides}
    return await client.post(url, headers=headers, json=payload)


async def _upload(client, headers, url, content=PDF, content_type="application/pdf"):
    return await client.post(
        f"{url}/documents",
        headers=headers,
        data={"title": "Blood panel"},
        files={"file": ("panel.pdf", content, content_type)},
    )


async def _titles(client, headers, url) -> list[str]:
    return [r["title"] for r in (await client.get(url, headers=headers)).json()["data"]]


async def test_veterinarian_adds_clinical_records_for_a_patient(client, scene):
    for record_type in ("diagnosis", "prescription", "labResult", "note"):
        resp = await _add(client, scene["vet"], scene["url"], type=record_type, title=record_type)
        assert resp.status_code == 201
        assert resp.json()["data"]["authored_by_vet"] is True
        assert resp.json()["data"]["author_name"] == "Dr. Sarah Jenkins"

    assert len(await _titles(client, scene["owner"], scene["url"])) == 4


async def test_owner_can_add_a_note_but_not_a_clinical_record(client, scene):
    note = await _add(client, scene["owner"], scene["url"])
    diagnosis = await _add(client, scene["owner"], scene["url"], type="diagnosis")

    assert note.status_code == 201
    assert note.json()["data"]["authored_by_vet"] is False
    assert diagnosis.status_code == 403


async def test_records_are_listed_newest_first_by_their_date(client, scene):
    await _add(client, scene["vet"], scene["url"], title="Old", date="2025-01-10T09:00:00Z")
    await _add(client, scene["vet"], scene["url"], title="New", date="2026-03-02T09:00:00Z")
    await _add(client, scene["vet"], scene["url"], title="Middle", date="2025-08-20T09:00:00Z")

    assert await _titles(client, scene["owner"], scene["url"]) == ["New", "Middle", "Old"]


async def test_veterinarian_is_refused_for_a_dog_that_is_not_their_patient(
    client, scene, db_session
):
    other_vet, _ = await verified_vet(client, db_session, "other-vet@example.com", "Dr. Other")

    assert (await client.get(scene["url"], headers=other_vet)).status_code == 404
    assert (await _add(client, other_vet, scene["url"], type="diagnosis")).status_code == 404
    assert (await _upload(client, other_vet, scene["url"])).status_code == 404


async def test_other_owners_cannot_read_records(client, scene):
    await _add(client, scene["vet"], scene["url"], type="diagnosis", title="Private")
    stranger = await owner_headers(client, "stranger@example.com")

    assert (await client.get(scene["url"], headers=stranger)).status_code == 404


async def test_owner_uploads_and_downloads_a_document(client, scene):
    resp = await _upload(client, scene["owner"], scene["url"])

    assert resp.status_code == 201
    record = resp.json()["data"]
    assert record["type"] == "document"
    assert record["title"] == "Blood panel"
    assert record["attachment_url"] == f"{scene['url']}/{record['id']}/attachment"
    download = await client.get(record["attachment_url"], headers=scene["owner"])
    assert download.content == PDF
    assert download.headers["content-type"] == "application/pdf"


async def test_treating_veterinarian_can_download_the_document(client, scene, db_session):
    record = (await _upload(client, scene["owner"], scene["url"], PNG, "image/png")).json()["data"]
    other_vet, _ = await verified_vet(client, db_session, "other-vet@example.com", "Dr. Other")

    assert (await client.get(record["attachment_url"], headers=scene["vet"])).content == PNG
    assert (await client.get(record["attachment_url"], headers=other_vet)).status_code == 404


async def test_unsupported_documents_are_rejected(client, scene):
    resp = await _upload(client, scene["owner"], scene["url"], b"MZ\x90\x00", "application/pdf")

    assert resp.status_code == 415
    assert await _titles(client, scene["owner"], scene["url"]) == []


async def test_records_without_attachment_have_no_download(client, scene):
    record = (await _add(client, scene["owner"], scene["url"])).json()["data"]

    assert record["attachment_url"] is None
    resp = await client.get(f"{scene['url']}/{record['id']}/attachment", headers=scene["owner"])
    assert resp.status_code == 404


async def test_only_the_author_can_delete_a_record(client, scene):
    by_vet = (await _add(client, scene["vet"], scene["url"], type="diagnosis")).json()["data"]
    by_owner = (await _upload(client, scene["owner"], scene["url"])).json()["data"]

    refused = await client.delete(f"{scene['url']}/{by_vet['id']}", headers=scene["owner"])
    deleted = await client.delete(f"{scene['url']}/{by_owner['id']}", headers=scene["owner"])

    assert refused.status_code == 403
    assert deleted.status_code == 200
    assert await _titles(client, scene["owner"], scene["url"]) == ["Observation"]
    gone = await client.get(by_owner["attachment_url"], headers=scene["owner"])
    assert gone.status_code == 404

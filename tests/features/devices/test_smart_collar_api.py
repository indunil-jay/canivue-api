import pytest

from tests.helpers import create_dog, owner_headers


@pytest.fixture
async def scene(client):
    owner = await owner_headers(client)
    dog = await create_dog(client, owner)
    return {"owner": owner, "dog": dog, "url": f"/api/v1/dogs/{dog['id']}/device"}


async def _get(client, scene) -> dict:
    return (await client.get(scene["url"], headers=scene["owner"])).json()["data"]


async def _post(client, scene, action, json=None):
    return await client.post(f"{scene['url']}/{action}", headers=scene["owner"], json=json)


async def test_a_dog_without_a_collar_reports_not_paired(client, scene):
    collar = await _get(client, scene)

    assert collar["state"] == "notPaired"
    assert collar["dog_id"] == scene["dog"]["id"]
    assert collar["battery_percent"] is None
    assert collar["last_synced_at"] is None
    assert collar["sync_history"] == []


async def test_pairing_connects_the_collar(client, scene):
    resp = await _post(client, scene, "pair")

    assert resp.status_code == 200
    assert resp.json()["data"]["state"] == "connected"
    assert (await _get(client, scene))["state"] == "connected"
    assert (await _get(client, scene))["granted_permissions"] == [
        "Activity & Motion", "Heart Rate", "Location",
    ]  # fmt: skip


async def test_owner_renames_a_paired_collar(client, scene):
    await _post(client, scene, "pair")

    resp = await client.patch(scene["url"], headers=scene["owner"], json={"name": "Buddy's Collar"})

    assert resp.json()["data"]["name"] == "Buddy's Collar"
    assert (await _get(client, scene))["name"] == "Buddy's Collar"


async def test_syncing_records_history_newest_first_and_battery(client, scene):
    await _post(client, scene, "pair")

    await _post(client, scene, "sync", {"records_synced": 120, "battery_percent": 82})
    resp = await _post(client, scene, "sync", {"records_synced": 45, "battery_percent": 80})

    collar = resp.json()["data"]
    assert [e["records_synced"] for e in collar["sync_history"]] == [45, 120]
    assert collar["battery_percent"] == 80
    assert collar["last_synced_at"] == collar["sync_history"][0]["timestamp"]


async def test_sync_without_a_body_is_accepted(client, scene):
    await _post(client, scene, "pair")

    resp = await _post(client, scene, "sync")

    assert resp.status_code == 200
    assert resp.json()["data"]["sync_history"][0]["records_synced"] == 0


async def test_disconnecting_stops_syncing_until_paired_again(client, scene):
    await _post(client, scene, "pair")
    await _post(client, scene, "sync", {"records_synced": 5})

    assert (await _post(client, scene, "disconnect")).json()["data"]["state"] == "disconnected"
    assert (await _post(client, scene, "sync")).status_code == 409

    assert (await _post(client, scene, "pair")).json()["data"]["state"] == "connected"
    assert len((await _get(client, scene))["sync_history"]) == 1


async def test_an_unpaired_collar_cannot_be_renamed_disconnected_or_synced(client, scene):
    rename = await client.patch(scene["url"], headers=scene["owner"], json={"name": "X"})

    assert rename.status_code == 409
    assert (await _post(client, scene, "disconnect")).status_code == 409
    assert (await _post(client, scene, "sync")).status_code == 409


async def test_other_owners_cannot_reach_the_collar(client, scene):
    stranger = await owner_headers(client, "stranger@example.com")

    assert (await client.get(scene["url"], headers=stranger)).status_code == 404
    assert (await client.post(f"{scene['url']}/pair", headers=stranger)).status_code == 404
    assert (await _get(client, scene))["state"] == "notPaired"

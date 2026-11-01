from datetime import datetime, timedelta, timezone

import pytest

from tests.helpers import create_dog, owner_headers


def _in(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


@pytest.fixture
async def scene(client):
    owner = await owner_headers(client)
    dog = await create_dog(client, owner)
    return {"owner": owner, "url": f"/api/v1/dogs/{dog['id']}/care-tasks"}


async def _add(client, scene, title="Rabies booster", category="vaccination", days=7):
    resp = await client.post(
        scene["url"],
        headers=scene["owner"],
        json={"category": category, "title": title, "due_date": _in(days)},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _list(client, scene) -> list[dict]:
    return (await client.get(scene["url"], headers=scene["owner"])).json()["data"]


async def test_owner_adds_a_care_task(client, scene):
    task = await _add(client, scene)

    assert task["category"] == "vaccination"
    assert task["title"] == "Rabies booster"
    assert task["completed"] is False
    assert task["is_overdue"] is False


async def test_every_category_is_accepted(client, scene):
    categories = [
        "vaccination", "deworming", "fleaTick", "dental",
        "grooming", "annualCheck", "weightGoal", "medication",
    ]  # fmt: skip

    for category in categories:
        await _add(client, scene, category=category)

    assert sorted(t["category"] for t in await _list(client, scene)) == sorted(categories)


async def test_tasks_past_their_due_date_are_overdue(client, scene):
    await _add(client, scene, title="Late", days=-3)

    assert (await _list(client, scene))[0]["is_overdue"] is True


async def test_outstanding_tasks_come_first_soonest_due_first(client, scene):
    await _add(client, scene, title="Later", days=30)
    done = await _add(client, scene, title="Done", days=1)
    await _add(client, scene, title="Soon", days=2)
    await client.post(f"{scene['url']}/{done['id']}/complete", headers=scene["owner"])

    assert [t["title"] for t in await _list(client, scene)] == ["Soon", "Later", "Done"]


async def test_completing_a_task_clears_overdue(client, scene):
    task = await _add(client, scene, days=-3)

    resp = await client.post(f"{scene['url']}/{task['id']}/complete", headers=scene["owner"])

    completed = resp.json()["data"]
    assert completed["completed"] is True
    assert completed["completed_at"] is not None
    assert completed["is_overdue"] is False


async def test_owner_removes_a_task(client, scene):
    task = await _add(client, scene)

    assert (
        await client.delete(f"{scene['url']}/{task['id']}", headers=scene["owner"])
    ).status_code == 200

    assert await _list(client, scene) == []


async def test_other_owners_cannot_see_or_change_tasks(client, scene):
    task = await _add(client, scene)
    stranger = await owner_headers(client, "stranger@example.com")

    assert (await client.get(scene["url"], headers=stranger)).status_code == 404
    complete = await client.post(f"{scene['url']}/{task['id']}/complete", headers=stranger)
    assert complete.status_code == 404


async def test_a_task_cannot_be_completed_through_another_dog(client, scene):
    task = await _add(client, scene)
    other_dog = await create_dog(client, scene["owner"], name="Luna")

    resp = await client.post(
        f"/api/v1/dogs/{other_dog['id']}/care-tasks/{task['id']}/complete", headers=scene["owner"]
    )

    assert resp.status_code == 404

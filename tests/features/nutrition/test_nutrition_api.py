from datetime import datetime, timedelta, timezone

import pytest

from tests.helpers import create_dog, owner_headers, record_readings

NOW = datetime.now(timezone.utc)


@pytest.fixture
async def scene(client):
    owner = await owner_headers(client)
    dog = await create_dog(client, owner, weight_kg=20.0)
    return {"owner": owner, "dog": dog, "url": f"/api/v1/dogs/{dog['id']}/nutrition"}


async def _profile(client, scene) -> dict:
    resp = await client.get(scene["url"], headers=scene["owner"])
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def test_profile_defaults_come_from_the_dogs_profile_weight(client, scene):
    profile = await _profile(client, scene)

    assert profile == {
        "current_weight_kg": 20.0,
        "weight_goal_kg": 20.0,
        "thirty_day_weight_change_kg": 0.0,
        "body_condition_score": 5,
        # 70 x 20^0.75 x 1.6
        "daily_calorie_target": 1059,
        "feeding_schedule": [],
        "nutrition_goal": "Maintain a healthy weight",
    }


async def test_weight_readings_drive_current_weight_and_thirty_day_change(client, scene):
    await record_readings(
        client, scene, "weight",
        [
            (25.0, NOW - timedelta(days=60)),
            (22.0, NOW - timedelta(days=25)),
            (21.4, NOW - timedelta(days=10)),
            (21.0, NOW - timedelta(days=1)),
        ],
    )  # fmt: skip

    profile = await _profile(client, scene)

    assert profile["current_weight_kg"] == 21.0
    assert profile["thirty_day_weight_change_kg"] == -1.0


async def test_owner_sets_goal_calories_and_feeding_schedule(client, scene):
    resp = await client.patch(
        scene["url"],
        headers=scene["owner"],
        json={
            "weight_goal_kg": 18.5,
            "daily_calorie_target": 900,
            "body_condition_score": 6,
            "nutrition_goal": "Lose 1.5 kg gradually",
            "feeding_schedule": [
                {"time": "18:30", "food_name": "Salmon kibble", "portion_grams": 140},
                {"time": "07:30", "food_name": "Salmon kibble", "portion_grams": 120},
            ],
        },
    )

    assert resp.status_code == 200
    profile = await _profile(client, scene)
    assert profile["weight_goal_kg"] == 18.5
    assert profile["daily_calorie_target"] == 900
    assert profile["body_condition_score"] == 6
    assert profile["nutrition_goal"] == "Lose 1.5 kg gradually"
    assert [e["time"] for e in profile["feeding_schedule"]] == ["07:30", "18:30"]
    assert profile["feeding_schedule"][0]["portion_grams"] == 120


async def test_calorie_target_follows_the_weight_goal_until_set(client, scene):
    await client.patch(scene["url"], headers=scene["owner"], json={"weight_goal_kg": 10})

    # 70 x 10^0.75 x 1.6
    assert (await _profile(client, scene))["daily_calorie_target"] == 630


async def test_partial_update_keeps_the_rest_of_the_plan(client, scene):
    await client.patch(scene["url"], headers=scene["owner"], json={"weight_goal_kg": 18.5})

    await client.patch(scene["url"], headers=scene["owner"], json={"body_condition_score": 7})

    profile = await _profile(client, scene)
    assert profile["weight_goal_kg"] == 18.5
    assert profile["body_condition_score"] == 7


@pytest.mark.parametrize(
    "bad",
    [
        {"body_condition_score": 10},
        {"weight_goal_kg": 0},
        {"feeding_schedule": [{"time": "7pm", "food_name": "Kibble", "portion_grams": 100}]},
        {"feeding_schedule": [{"time": "07:00", "food_name": "Kibble", "portion_grams": 0}]},
    ],
)
async def test_invalid_plans_are_rejected(client, scene, bad):
    assert (await client.patch(scene["url"], headers=scene["owner"], json=bad)).status_code == 422


async def test_other_owners_cannot_read_or_change_the_plan(client, scene):
    stranger = await owner_headers(client, "stranger@example.com")

    assert (await client.get(scene["url"], headers=stranger)).status_code == 404
    patch = await client.patch(scene["url"], headers=stranger, json={"weight_goal_kg": 5})
    assert patch.status_code == 404
    assert (await _profile(client, scene))["weight_goal_kg"] == 20.0

from datetime import datetime, timedelta, timezone

import pytest

from tests.helpers import create_dog, owner_headers, record_readings

NOW = datetime.now(timezone.utc)
NOON = NOW.replace(hour=12, minute=0, second=0, microsecond=0)


def days_ago(days: int, hour: int = 12) -> datetime:
    return (NOW - timedelta(days=days)).replace(hour=hour, minute=0, second=0, microsecond=0)


@pytest.fixture
async def scene(client):
    owner = await owner_headers(client)
    dog = await create_dog(client, owner)
    return {"owner": owner, "dog": dog, "url": f"/api/v1/dogs/{dog['id']}/metrics"}


async def _series(client, scene, metric, time_range="weekly") -> dict:
    resp = await client.get(
        f"{scene['url']}/{metric}", headers=scene["owner"], params={"range": time_range}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def test_a_dog_with_no_readings_has_an_empty_series(client, scene):
    series = await _series(client, scene, "heartRate")

    assert series == {
        "metric": "heartRate",
        "range": "weekly",
        "points": [],
        "baseline_average": 0.0,
    }


async def test_weekly_series_averages_vitals_per_day(client, scene):
    await record_readings(
        client, scene, "heartRate",
        [(80, days_ago(2, 8)), (100, days_ago(2, 18)), (90, days_ago(1))],
    )  # fmt: skip

    series = await _series(client, scene, "heartRate")

    assert [p["value"] for p in series["points"]] == [90.0, 90.0]
    assert series["baseline_average"] == 90.0
    assert not any(p["is_abnormal"] for p in series["points"])


async def test_cumulative_metrics_are_summed_per_day(client, scene):
    await record_readings(
        client, scene, "activity",
        [(3000, days_ago(1, 8)), (4500, days_ago(1, 17)), (6000, days_ago(2))],
    )  # fmt: skip

    series = await _series(client, scene, "activity")

    assert [p["value"] for p in series["points"]] == [6000.0, 7500.0]


async def test_points_are_in_time_order_with_empty_days_left_out(client, scene):
    await record_readings(
        client, scene, "weight", [(28.5, days_ago(1)), (28.0, days_ago(5)), (28.2, days_ago(3))]
    )

    series = await _series(client, scene, "weight")

    assert [p["value"] for p in series["points"]] == [28.0, 28.2, 28.5]
    dates = [p["date"] for p in series["points"]]
    assert dates == sorted(dates)


async def test_values_far_from_the_dogs_baseline_are_flagged(client, scene):
    history = [(80, days_ago(d)) for d in range(10, 40)]
    await record_readings(client, scene, "heartRate", history)
    await record_readings(client, scene, "heartRate", [(82, days_ago(2)), (120, days_ago(1))])

    series = await _series(client, scene, "heartRate")

    assert series["baseline_average"] == 80.0
    assert [(p["value"], p["is_abnormal"]) for p in series["points"]] == [
        (82.0, False),
        (120.0, True),
    ]


async def test_temperature_uses_a_tighter_tolerance(client, scene):
    await record_readings(
        client, scene, "temperature", [(38.5, days_ago(d)) for d in range(10, 30)]
    )
    await record_readings(client, scene, "temperature", [(38.9, days_ago(2)), (39.8, days_ago(1))])

    series = await _series(client, scene, "temperature")

    assert [p["is_abnormal"] for p in series["points"]] == [False, True]


async def test_ranges_cover_different_windows(client, scene):
    await record_readings(
        client, scene, "weight",
        [(28.0, days_ago(20)), (28.4, days_ago(3)), (28.6, NOW - timedelta(hours=2))],
    )  # fmt: skip

    daily = await _series(client, scene, "weight", "daily")
    weekly = await _series(client, scene, "weight", "weekly")
    monthly = await _series(client, scene, "weight", "monthly")

    assert [p["value"] for p in daily["points"]] == [28.6]
    assert [p["value"] for p in weekly["points"]] == [28.4, 28.6]
    assert [p["value"] for p in monthly["points"]] == [28.0, 28.4, 28.6]


async def test_metrics_are_kept_separate(client, scene):
    await record_readings(client, scene, "heartRate", [(90, days_ago(1))])

    assert (await _series(client, scene, "sleep"))["points"] == []


async def test_reading_without_a_timestamp_is_recorded_now(client, scene):
    resp = await client.post(
        f"{scene['url']}/hydration/readings",
        headers=scene["owner"],
        json={"readings": [{"value": 250}]},
    )

    assert resp.status_code == 201
    assert resp.json()["data"] == {"stored": 1}
    assert len((await _series(client, scene, "hydration", "daily"))["points"]) == 1


@pytest.mark.parametrize(
    ("metric", "value"),
    [("heartRate", 900), ("temperature", 12), ("sleep", 30), ("weight", -1), ("activity", -5)],
)
async def test_implausible_values_are_rejected(client, scene, metric, value):
    resp = await client.post(
        f"{scene['url']}/{metric}/readings",
        headers=scene["owner"],
        json={"readings": [{"value": value}]},
    )

    assert resp.status_code == 422


async def test_a_batch_with_one_bad_reading_stores_nothing(client, scene):
    resp = await client.post(
        f"{scene['url']}/heartRate/readings",
        headers=scene["owner"],
        json={"readings": [{"value": 90}, {"value": 9000}]},
    )

    assert resp.status_code == 422
    assert (await _series(client, scene, "heartRate", "daily"))["points"] == []


async def test_future_dated_readings_are_rejected(client, scene):
    tomorrow = (NOW + timedelta(days=1)).isoformat()

    resp = await client.post(
        f"{scene['url']}/heartRate/readings",
        headers=scene["owner"],
        json={"readings": [{"value": 90, "recorded_at": tomorrow}]},
    )

    assert resp.status_code == 422


async def test_unknown_metrics_and_ranges_are_rejected(client, scene):
    unknown_metric = await client.get(f"{scene['url']}/mood", headers=scene["owner"])
    unknown_range = await client.get(
        f"{scene['url']}/weight", headers=scene["owner"], params={"range": "yearly"}
    )

    assert unknown_metric.status_code == 422
    assert unknown_range.status_code == 422


async def test_other_owners_cannot_read_or_write_metrics(client, scene):
    stranger = await owner_headers(client, "stranger@example.com")

    read = await client.get(f"{scene['url']}/weight", headers=stranger)
    write = await client.post(
        f"{scene['url']}/weight/readings", headers=stranger, json={"readings": [{"value": 20}]}
    )

    assert read.status_code == 404
    assert write.status_code == 404

from datetime import datetime, timedelta, timezone

import pytest

from tests.helpers import (
    book_appointment,
    create_dog,
    next_weekday,
    owner_headers,
    record_readings,
    verified_vet,
)

NOW = datetime.now(timezone.utc)
ITCHY = "Buddy has been scratching his ear and the redness is getting worse for three days"


def _in(days: int) -> str:
    return (NOW + timedelta(days=days)).isoformat()


@pytest.fixture
async def scene(client):
    owner = await owner_headers(client, full_name="Alex Taylor")
    dog = await create_dog(
        client,
        owner,
        weight_kg=20.0,
        vaccinations=[
            {"name": "Rabies", "date_given": "2025-06-01", "next_due_date": "2026-06-01"}
        ],
    )
    return {"owner": owner, "dog": dog, "base": f"/api/v1/dogs/{dog['id']}"}


async def _get(client, scene, path, headers=None):
    resp = await client.get(f"{scene['base']}/{path}", headers=headers or scene["owner"])
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _health_check(client, scene, text=ITCHY):
    resp = await client.post(
        f"{scene['base']}/health-checks", headers=scene["owner"], data={"symptom_text": text}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _add_task(client, scene, title, category, days):
    resp = await client.post(
        f"{scene['base']}/care-tasks",
        headers=scene["owner"],
        json={"category": category, "title": title, "due_date": _in(days)},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def test_dashboard_for_a_new_dog_has_no_score_and_empty_sections(client, scene):
    dashboard = await _get(client, scene, "dashboard")

    assert dashboard["health_score"] is None
    assert dashboard["vitals"] == {
        "heart_rate_bpm": None,
        "temperature_c": None,
        "activity_steps_today": 0,
        "activity_goal_steps": 8000,
        "sleep_hours_last_night": None,
        "hydration_ml": 0,
        "hydration_goal_ml": 1200,
        "weight_kg": 20.0,
    }
    assert dashboard["insight"]["risk"] == "normal"
    assert dashboard["insight"]["headline"] == "No concerns on record"
    assert dashboard["reminders"] == []
    assert dashboard["appointment"] is None
    assert dashboard["device"]["state"] == "notPaired"


async def test_dashboard_vitals_come_from_the_latest_readings(client, scene):
    recent = NOW - timedelta(minutes=5)
    await record_readings(
        client, scene, "heartRate", [(80, NOW - timedelta(hours=3)), (96, recent)]
    )
    await record_readings(client, scene, "temperature", [(38.6, recent)])
    await record_readings(client, scene, "weight", [(21.5, recent)])
    await record_readings(client, scene, "sleep", [(7.5, NOW - timedelta(hours=6))])

    vitals = (await _get(client, scene, "dashboard"))["vitals"]

    assert vitals["heart_rate_bpm"] == 96
    assert vitals["temperature_c"] == 38.6
    assert vitals["weight_kg"] == 21.5
    assert vitals["hydration_goal_ml"] == 1290
    assert vitals["sleep_hours_last_night"] == 7.5


async def test_dashboard_totals_todays_activity_and_hydration(client, scene):
    just_now = datetime.now(timezone.utc)
    await record_readings(
        client,
        scene,
        "activity",
        [(1200, just_now), (800, just_now), (9000, NOW - timedelta(days=2))],
    )
    await record_readings(client, scene, "hydration", [(250, just_now), (300, just_now)])

    vitals = (await _get(client, scene, "dashboard"))["vitals"]

    assert vitals["activity_steps_today"] == 2000
    assert vitals["hydration_ml"] == 550


async def test_dashboard_insight_and_score_follow_the_latest_prediction(client, scene):
    result = await _health_check(client, scene)

    dashboard = await _get(client, scene, "dashboard")

    assert dashboard["insight"] == {
        "headline": "Suspected Ear Infection",
        "detail": result["progression"]["recommendation"],
        "risk": "elevated",
    }
    assert dashboard["health_score"] == round(100 - result["progression"]["risk_percent"] * 0.5)


async def test_dashboard_score_drops_for_a_vital_off_baseline(client, scene):
    await record_readings(
        client, scene, "heartRate", [(80, NOW - timedelta(days=d)) for d in range(10, 30)]
    )
    await record_readings(client, scene, "heartRate", [(80, NOW - timedelta(days=1))])
    assert (await _get(client, scene, "dashboard"))["health_score"] == 100

    await record_readings(client, scene, "heartRate", [(140, NOW - timedelta(minutes=1))])

    assert (await _get(client, scene, "dashboard"))["health_score"] == 95


async def test_dashboard_reminders_are_the_next_outstanding_care_tasks(client, scene):
    await _add_task(client, scene, "Annual check", "annualCheck", 40)
    done = await _add_task(client, scene, "Old booster", "vaccination", -30)
    await _add_task(client, scene, "Flea treatment", "fleaTick", -2)
    await _add_task(client, scene, "Deworming", "deworming", 5)
    await _add_task(client, scene, "Nail trim", "grooming", 10)
    await client.post(f"{scene['base']}/care-tasks/{done['id']}/complete", headers=scene["owner"])

    reminders = (await _get(client, scene, "dashboard"))["reminders"]

    assert [(r["title"], r["kind"], r["is_overdue"]) for r in reminders] == [
        ("Flea treatment", "checkup", True),
        ("Deworming", "deworming", False),
        ("Nail trim", "grooming", False),
    ]


async def test_dashboard_shows_the_next_live_appointment(client, scene, db_session):
    _, vet_id = await verified_vet(client, db_session, clinics=["Bay Area Vet"])
    booking = {**scene, "vet_id": vet_id}
    sooner = await book_appointment(client, booking, when=next_weekday(0, hour=9))
    later = await book_appointment(
        client, booking, when=next_weekday(0, hour=15), consultation_type="chat"
    )

    first = (await _get(client, scene, "dashboard"))["appointment"]
    await client.post(f"/api/v1/appointments/{sooner['id']}/cancel", headers=scene["owner"])
    second = (await _get(client, scene, "dashboard"))["appointment"]

    assert first == {
        "vet_name": "Dr. Sarah Jenkins",
        "clinic": "Bay Area Vet",
        "time": sooner["date_time"],
        "is_video_call": True,
    }
    assert second["time"] == later["date_time"]
    assert second["is_video_call"] is False


async def test_dashboard_reports_the_collar(client, scene):
    await client.post(f"{scene['base']}/device/pair", headers=scene["owner"])
    await client.post(
        f"{scene['base']}/device/sync", headers=scene["owner"], json={"battery_percent": 64}
    )

    device = (await _get(client, scene, "dashboard"))["device"]

    assert device["state"] == "connected"
    assert device["battery_percent"] == 64
    assert device["last_synced_at"] is not None


async def test_timeline_merges_every_source_newest_first(client, scene, db_session):
    vet, vet_id = await verified_vet(client, db_session)
    await book_appointment(client, {**scene, "vet_id": vet_id})
    await client.post(
        f"{scene['base']}/records",
        headers=vet,
        json={"type": "diagnosis", "title": "Otitis externa", "date": "2026-02-01T10:00:00Z"},
    )
    await client.post(
        f"{scene['base']}/records",
        headers=vet,
        json={"type": "prescription", "title": "Ear drops", "date": "2026-02-01T10:05:00Z"},
    )
    await client.post(
        f"{scene['base']}/records", headers=scene["owner"], json={"type": "note", "title": "Diary"}
    )
    await _health_check(client, scene)
    await _health_check(client, scene, "Just a routine check, he seems fine and happy")
    await record_readings(
        client, scene, "weight", [(20.0, NOW - timedelta(days=9)), (21.0, NOW - timedelta(days=2))]
    )
    task = await _add_task(client, scene, "Heartworm tablet", "medication", 1)
    await client.post(f"{scene['base']}/care-tasks/{task['id']}/complete", headers=scene["owner"])

    timeline = await _get(client, scene, "timeline")

    by_type = {}
    for event in timeline:
        by_type.setdefault(event["type"], []).append(event["title"])
    assert by_type["vaccination"] == ["Rabies vaccination"]
    assert by_type["diagnosis"] == ["Otitis externa"]
    assert sorted(by_type["medication"]) == ["Ear drops", "Heartworm tablet"]
    assert by_type["appointment"] == ["Appointment with Dr. Sarah Jenkins"]
    assert by_type["healthAlert"] == ["Suspected Ear Infection"]
    assert by_type["aiPrediction"] == ["General Wellness Check"]
    assert by_type["weightChange"] == ["Weight 21.0 kg"]
    assert "Diary" not in [e["title"] for e in timeline]
    dates = [e["date"] for e in timeline]
    assert dates == sorted(dates, reverse=True)


async def test_timeline_includes_readings_off_baseline(client, scene):
    await record_readings(
        client, scene, "heartRate", [(80, NOW - timedelta(days=d)) for d in range(10, 30)]
    )
    await record_readings(client, scene, "heartRate", [(130, NOW - timedelta(days=1))])

    sensor_events = [e for e in await _get(client, scene, "timeline") if e["type"] == "sensorEvent"]

    assert [e["title"] for e in sensor_events] == ["Heart rate above baseline"]
    assert "130 bpm against a baseline of 80 bpm" in sensor_events[0]["description"]


async def test_cancelled_appointments_are_left_off_the_timeline(client, scene, db_session):
    _, vet_id = await verified_vet(client, db_session)
    appointment = await book_appointment(client, {**scene, "vet_id": vet_id})
    await client.post(f"/api/v1/appointments/{appointment['id']}/cancel", headers=scene["owner"])

    types = [e["type"] for e in await _get(client, scene, "timeline")]

    assert "appointment" not in types


async def test_insights_are_empty_without_two_months_of_history(client, scene):
    await record_readings(client, scene, "activity", [(5000, NOW - timedelta(days=3))])

    assert await _get(client, scene, "insights") == []


async def test_insights_describe_month_on_month_trends(client, scene):
    last_month = [NOW - timedelta(days=d) for d in range(35, 55)]
    this_month = [NOW - timedelta(days=d) for d in range(2, 22)]
    await record_readings(client, scene, "activity", [(5000, at) for at in last_month])
    await record_readings(client, scene, "activity", [(6000, at) for at in this_month])
    await record_readings(client, scene, "heartRate", [(100, at) for at in last_month])
    await record_readings(client, scene, "heartRate", [(120, at) for at in this_month])
    await record_readings(client, scene, "weight", [(20.0, at) for at in last_month])
    await record_readings(client, scene, "weight", [(20.2, at) for at in this_month])

    insights = {i["headline"]: i for i in await _get(client, scene, "insights")}

    activity = insights["Activity increased 20% this month"]
    assert (activity["direction"], activity["is_positive"]) == ("up", True)
    heart = insights["Resting heart rate increased 20% this month"]
    assert (heart["direction"], heart["is_positive"]) == ("up", False)
    weight = insights["Weight is steady"]
    assert (weight["direction"], weight["is_positive"]) == ("stable", True)
    assert "Buddy" in activity["detail"]


async def test_read_models_are_private_to_those_who_can_reach_the_dog(client, scene):
    stranger = await owner_headers(client, "stranger@example.com")

    for path in ("dashboard", "timeline", "insights"):
        resp = await client.get(f"{scene['base']}/{path}", headers=stranger)
        assert resp.status_code == 404

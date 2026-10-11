from datetime import datetime, timedelta, timezone

import pytest

from tests.helpers import book_appointment, create_dog, next_weekday, owner_headers, verified_vet

PORTAL = "/api/v1/vet-portal"
VETS = "/api/v1/veterinarians"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ITCHY = "Buddy has been scratching his ear and the redness is getting worse for three days"


@pytest.fixture
async def scene(client, db_session):
    owner = await owner_headers(client, full_name="Alex Taylor")
    dog = await create_dog(
        client,
        owner,
        allergies=["Wheat"],
        existing_conditions=["Hip dysplasia"],
        medications=[{"name": "Joint chews", "dosage": "1", "frequency": "Daily"}],
    )
    vet, vet_id = await verified_vet(client, db_session)
    return {"owner": owner, "dog": dog, "vet": vet, "vet_id": vet_id}


async def _dashboard(client, headers) -> dict:
    resp = await client.get(f"{PORTAL}/dashboard", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _patients(client, headers) -> list[dict]:
    resp = await client.get(f"{PORTAL}/patients", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _health_check(client, scene, text=ITCHY):
    await client.post(
        f"/api/v1/dogs/{scene['dog']['id']}/health-checks",
        headers=scene["owner"],
        data={"symptom_text": text},
    )


async def test_an_idle_veterinarian_has_an_empty_dashboard(client, scene):
    dashboard = await _dashboard(client, scene["vet"])

    assert dashboard == {
        "vet_name": "Dr. Sarah Jenkins",
        "today_schedule": [],
        "waiting_consultation_count": 0,
        "critical_alert_count": 0,
        "new_patient_count": 0,
        "recent_messages": [],
    }
    assert await _patients(client, scene["vet"]) == []


async def test_dashboard_counts_requests_and_new_patients(client, scene):
    first = await book_appointment(client, scene, when=next_weekday(0, hour=9))
    await book_appointment(client, scene, when=next_weekday(0, hour=11))
    await client.post(f"/api/v1/appointments/{first['id']}/confirm", headers=scene["vet"])

    dashboard = await _dashboard(client, scene["vet"])

    assert dashboard["waiting_consultation_count"] == 1
    assert dashboard["new_patient_count"] == 1
    assert dashboard["today_schedule"] == []


async def test_todays_schedule_lists_todays_appointments_in_order(client, scene):
    now = datetime.now(timezone.utc)
    later_today = (now + timedelta(minutes=5)).replace(second=0, microsecond=0)
    if later_today.date() != now.date():
        pytest.skip("too close to midnight UTC to book another slot today")
    today = WEEKDAYS[now.weekday()]
    await client.put(
        f"{VETS}/me/availability/{today}", headers=scene["vet"], json={"available": True}
    )
    appointment = await book_appointment(client, scene, when=later_today, consultation_type="chat")
    await book_appointment(client, scene, when=next_weekday((now.weekday() + 1) % 7))

    schedule = (await _dashboard(client, scene["vet"]))["today_schedule"]

    assert schedule == [
        {
            "appointment_id": appointment["id"],
            "time": appointment["date_time"],
            "owner_name": "Alex Taylor",
            "dog_name": "Buddy",
            "type": "Chat",
            "confirmed": False,
        }
    ]


async def test_patient_list_carries_clinical_context(client, scene):
    appointment = await book_appointment(client, scene)

    patient = (await _patients(client, scene["vet"]))[0]

    assert patient["dog_id"] == scene["dog"]["id"]
    assert patient["dog_name"] == "Buddy"
    assert patient["breed"] == "Golden Retriever"
    assert "yrs" in patient["age_formatted"]
    assert patient["owner_name"] == "Alex Taylor"
    assert patient["allergies"] == ["Wheat"]
    assert patient["existing_conditions"] == ["Hip dysplasia"]
    assert patient["current_medications"] == ["Joint chews"]
    assert patient["last_visit"] is None
    assert (patient["needs_follow_up"], patient["has_critical_alert"]) == (False, False)

    for action in ("confirm", "complete"):
        await client.post(
            f"/api/v1/appointments/{appointment['id']}/{action}", headers=scene["vet"]
        )

    assert (await _patients(client, scene["vet"]))[0]["last_visit"] == appointment["date_time"]


async def test_high_risk_predictions_raise_critical_alerts_and_follow_ups(client, scene):
    appointment = await book_appointment(client, scene)
    await _health_check(client, scene)

    booked = (await _patients(client, scene["vet"]))[0]
    for action in ("confirm", "complete"):
        await client.post(
            f"/api/v1/appointments/{appointment['id']}/{action}", headers=scene["vet"]
        )
    after_visit = (await _patients(client, scene["vet"]))[0]

    assert (booked["has_critical_alert"], booked["needs_follow_up"]) == (True, False)
    assert (after_visit["has_critical_alert"], after_visit["needs_follow_up"]) == (True, True)
    assert (await _dashboard(client, scene["vet"]))["critical_alert_count"] == 1


async def test_patients_with_critical_alerts_are_listed_first(client, scene):
    await book_appointment(client, scene, when=next_weekday(0, hour=9))
    calm = await create_dog(client, scene["owner"], name="Archie")
    await book_appointment(client, {**scene, "dog": calm}, when=next_weekday(0, hour=11))
    await _health_check(client, scene)

    names = [p["dog_name"] for p in await _patients(client, scene["vet"])]

    assert names == ["Buddy", "Archie"]


async def test_cancelled_bookings_do_not_make_a_patient(client, scene):
    appointment = await book_appointment(client, scene)
    await client.post(f"/api/v1/appointments/{appointment['id']}/cancel", headers=scene["owner"])

    assert await _patients(client, scene["vet"]) == []
    assert (await _dashboard(client, scene["vet"]))["new_patient_count"] == 0


async def test_dashboard_shows_recent_conversations(client, scene):
    conversation = (
        await client.post(
            "/api/v1/conversations", headers=scene["owner"], json={"vet_id": scene["vet_id"]}
        )
    ).json()["data"]
    await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=scene["owner"],
        json={"text": "Buddy is limping"},
    )

    messages = (await _dashboard(client, scene["vet"]))["recent_messages"]

    assert [(m["owner_name"], m["preview"]) for m in messages] == [
        ("Alex Taylor", "Buddy is limping")
    ]
    assert messages[0]["conversation_id"] == conversation["id"]


async def test_each_veterinarian_sees_only_their_own_caseload(client, scene, db_session):
    await book_appointment(client, scene)
    other_vet, _ = await verified_vet(client, db_session, "other-vet@example.com", "Dr. Other")

    assert await _patients(client, other_vet) == []
    assert (await _dashboard(client, other_vet))["waiting_consultation_count"] == 0


async def test_the_portal_is_for_veterinarians_only(client, scene):
    assert (await client.get(f"{PORTAL}/dashboard", headers=scene["owner"])).status_code == 403
    assert (await client.get(f"{PORTAL}/patients", headers=scene["owner"])).status_code == 403
    assert (await client.get(f"{PORTAL}/dashboard")).status_code == 401

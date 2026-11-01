from datetime import datetime, timedelta, timezone

import pytest

from tests.helpers import (
    book_appointment,
    create_dog,
    owner_headers,
    record_readings,
    verified_vet,
)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
NOW = datetime.now(timezone.utc)
ITCHY = "Buddy has been scratching his ear and the redness is getting worse for three days"


@pytest.fixture
async def scene(client):
    owner = await owner_headers(client, full_name="Alex Taylor")
    dog = await create_dog(client, owner)
    return {"owner": owner, "dog": dog, "base": f"/api/v1/dogs/{dog['id']}"}


async def _check(client, scene, text=None, image=False, sensors=False, headers=None):
    data = {"use_sensor_data": str(sensors).lower()}
    if text is not None:
        data["symptom_text"] = text
    files = {"image": ("dog.png", PNG, "image/png")} if image else None
    return await client.post(
        f"{scene['base']}/health-checks",
        headers=headers or scene["owner"],
        data=data,
        files=files,
    )


async def _history(client, scene, headers=None) -> list[dict]:
    resp = await client.get(f"{scene['base']}/predictions", headers=headers or scene["owner"])
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


def _modalities(result: dict) -> dict:
    return {m["name"]: m for m in result["fusion"]["modalities"]}


async def test_assessment_from_symptom_text_alone(client, scene):
    resp = await _check(client, scene, text=ITCHY)

    assert resp.status_code == 201
    result = resp.json()["data"]
    assert result["dog_name"] == "Buddy"
    assert result["fusion"]["condition"] == "Suspected Ear Infection"
    assert result["fusion"]["category"] == "Ear"
    modalities = _modalities(result)
    assert modalities["Symptom Text"]["available"] is True
    assert modalities["Symptom Text"]["contribution_percent"] == 100.0
    assert modalities["Image"]["available"] is False
    assert modalities["Smart Collar"]["available"] is False
    assert "Image was unavailable" in " ".join(result["fusion"]["notes"])
    assert result["progression"]["horizon_days"] == 7
    assert result["progression"]["missing_data_note"] is not None
    assert "does not replace" in result["safety_notice"]
    assert result["model_version"] == "stub-fusion-v1"


async def test_assessment_from_a_photo_alone(client, scene):
    resp = await _check(client, scene, image=True)

    result = resp.json()["data"]
    assert resp.status_code == 201
    assert result["fusion"]["condition"] == "General Wellness Check"
    assert _modalities(result)["Image"]["contribution_percent"] == 100.0
    assert "No symptom description was provided." in result["fusion"]["notes"]


async def test_assessment_uses_collar_data_when_there_is_some(client, scene):
    await record_readings(
        client, scene, "heartRate", [(90, NOW - timedelta(days=d)) for d in range(1, 5)]
    )

    result = (await _check(client, scene, text=ITCHY, sensors=True)).json()["data"]

    modalities = _modalities(result)
    assert modalities["Smart Collar"]["available"] is True
    assert modalities["Smart Collar"]["contribution_percent"] > 0
    shares = [m["contribution_percent"] for m in modalities.values()]
    assert sum(shares) == pytest.approx(100.0, abs=0.2)
    assert result["progression"]["missing_data_note"] is None
    labels = [f["label"] for f in result["progression"]["factors"]]
    assert "Behavioural trend (collar)" in labels


async def test_requested_collar_data_that_does_not_exist_is_reported_missing(client, scene):
    result = (await _check(client, scene, text=ITCHY, sensors=True)).json()["data"]

    assert _modalities(result)["Smart Collar"]["available"] is False
    assert "Smart-collar data was unavailable" in " ".join(result["fusion"]["notes"])


async def test_all_three_modalities_share_the_contribution(client, scene):
    await record_readings(client, scene, "activity", [(5000, NOW - timedelta(days=1))])

    result = (await _check(client, scene, text=ITCHY, image=True, sensors=True)).json()["data"]

    assert all(m["available"] for m in result["fusion"]["modalities"])
    assert result["fusion"]["notes"] == []
    assert 0 < result["fusion"]["final_confidence_percent"] <= 100


async def test_assessment_without_any_evidence_is_rejected(client, scene):
    assert (await _check(client, scene)).status_code == 422
    assert (await _check(client, scene, text="   ", sensors=True)).status_code == 422
    assert await _history(client, scene) == []


async def test_progression_factors_explain_the_risk(client, scene):
    result = (await _check(client, scene, text=ITCHY)).json()["data"]
    progression = result["progression"]

    assert sum(f["weight_percent"] for f in progression["factors"]) == pytest.approx(100, abs=0.5)
    assert sum(f["contribution_points"] for f in progression["factors"]) == pytest.approx(
        progression["risk_percent"], abs=0.5
    )
    points = [f["contribution_points"] for f in progression["factors"]]
    assert points == sorted(points, reverse=True)
    assert progression["main_reasons"] == [f["label"] for f in progression["factors"][:3]]


@pytest.mark.parametrize(
    ("text", "level"),
    [
        ("Just a routine check, he seems fine and happy", "moderate"),
        (ITCHY, "high"),
    ],
)
async def test_risk_level_follows_the_thresholds(client, scene, text, level):
    progression = (await _check(client, scene, text=text)).json()["data"]["progression"]

    risk = progression["risk_percent"]
    expected = (
        "critical" if risk >= 85 else "high" if risk >= 60 else "moderate" if risk >= 30 else "low"
    )
    assert progression["risk_level"] == expected == level


async def test_emergency_wording_forces_a_critical_result(client, scene):
    resp = await _check(client, scene, text="He collapsed and is struggling to breathe, gums blue")

    progression = resp.json()["data"]["progression"]
    assert progression["risk_level"] == "critical"
    assert progression["risk_percent"] >= 85


async def test_each_assessment_is_stored_as_a_prediction(client, scene):
    first = (await _check(client, scene, text="He is limping on his back leg")).json()["data"]
    second = (await _check(client, scene, text=ITCHY)).json()["data"]

    history = await _history(client, scene)

    assert [p["id"] for p in history] == [second["prediction_id"], first["prediction_id"]]
    newest = history[0]
    assert newest["title"] == "Suspected Ear Infection"
    assert newest["status"] == "highRisk"
    assert newest["combined_risk_percent"] == second["progression"]["risk_percent"]
    assert newest["confidence_percent"] == second["fusion"]["final_confidence_percent"]
    assert newest["model_contributions"] == [
        {"model_name": "Symptom Text Model", "contribution_percent": 100.0}
    ]
    assert "1 of 3 evidence streams" in newest["data_quality_note"]
    assert "since the last check" in newest["historical_comparison_note"]
    assert "first health check" in history[1]["historical_comparison_note"]


async def test_latest_prediction_is_null_until_there_is_one(client, scene):
    url = f"{scene['base']}/predictions/latest"
    assert (await client.get(url, headers=scene["owner"])).json()["data"] is None

    result = (await _check(client, scene, text=ITCHY)).json()["data"]

    latest = (await client.get(url, headers=scene["owner"])).json()["data"]
    assert latest["id"] == result["prediction_id"]


async def test_the_full_assessment_can_be_fetched_again(client, scene):
    result = (await _check(client, scene, text=ITCHY, image=True)).json()["data"]

    resp = await client.get(
        f"{scene['base']}/predictions/{result['prediction_id']}", headers=scene["owner"]
    )

    assert resp.json()["data"] == result


async def test_high_risk_result_notifies_the_owner(client, scene):
    await _check(client, scene, text="Just a routine check, he seems fine and happy")
    inbox = (await client.get("/api/v1/notifications", headers=scene["owner"])).json()["data"]
    assert inbox["items"] == []

    await _check(client, scene, text=ITCHY)

    inbox = (await client.get("/api/v1/notifications", headers=scene["owner"])).json()["data"]
    assert inbox["items"][0]["type"] == "aiHealthAlert"
    assert inbox["items"][0]["title"] == "AI Health Alert: Suspected Ear Infection"
    assert inbox["items"][0]["dog_name"] == "Buddy"


async def test_treating_veterinarian_records_an_outcome_and_resolves(client, scene, db_session):
    result = (await _check(client, scene, text=ITCHY)).json()["data"]
    vet, vet_id = await verified_vet(client, db_session)
    url = f"{scene['base']}/predictions/{result['prediction_id']}/outcome"
    payload = {"outcome_note": "Confirmed otitis externa; drops prescribed.", "resolved": True}
    assert (await client.patch(url, headers=vet, json=payload)).status_code == 404
    assert (await client.patch(url, headers=scene["owner"], json=payload)).status_code == 404
    await book_appointment(client, {**scene, "vet_id": vet_id})

    resp = await client.patch(url, headers=vet, json=payload)

    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "resolved"
    assert resp.json()["data"]["outcome_note"] == "Confirmed otitis externa; drops prescribed."
    latest = await client.get(f"{scene['base']}/predictions/latest", headers=scene["owner"])
    assert latest.json()["data"] is None
    assert len(await _history(client, scene)) == 1


async def test_other_owners_cannot_run_or_read_assessments(client, scene):
    result = (await _check(client, scene, text=ITCHY)).json()["data"]
    stranger = await owner_headers(client, "stranger@example.com")

    assert (await _check(client, scene, text=ITCHY, headers=stranger)).status_code == 404
    assert (await client.get(f"{scene['base']}/predictions", headers=stranger)).status_code == 404
    detail = await client.get(
        f"{scene['base']}/predictions/{result['prediction_id']}", headers=stranger
    )
    assert detail.status_code == 404


async def test_a_non_image_upload_is_rejected(client, scene):
    resp = await client.post(
        f"{scene['base']}/health-checks",
        headers=scene["owner"],
        data={"symptom_text": ITCHY},
        files={"image": ("x.png", b"<html></html>", "image/png")},
    )

    assert resp.status_code == 415
    assert await _history(client, scene) == []

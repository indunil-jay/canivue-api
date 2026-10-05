import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_parse_symptoms_api_success(client: AsyncClient):
    payload = {
        "text": "My dog has been scratching its left ear for three days and it is becoming red."
    }
    response = await client.post("/api/v1/symptoms/parse", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert "scratching" in data["symptoms"]
    assert any(loc["part"] == "ear" for loc in data["body_locations"])
    assert data["duration"]["value"] == 3
    assert data["duration"]["unit"] == "days"
    assert "ear_inflammation" in data["condition_probabilities"]
    assert data["text_quality_score"] > 0.0
    assert data["model_confidence"] > 0.0
    assert data["emergency_triage"]["is_critical"] is False


@pytest.mark.asyncio
async def test_parse_symptoms_api_empty_text(client: AsyncClient):
    payload = {"text": "   "}
    response = await client.post("/api/v1/symptoms/parse", json=payload)
    assert response.status_code == 400

    body = response.json()
    assert body["success"] is False
    assert body["error"]["message"] == "Symptom description text cannot be empty."

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


@pytest.mark.asyncio
async def test_parse_symptoms_api_emergency_alert(client: AsyncClient):
    payload = {"text": "My dog collapsed and is gasping for air."}
    response = await client.post("/api/v1/symptoms/parse", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    triage = body["data"]["emergency_triage"]
    assert triage["is_critical"] is True
    assert "Sudden collapse" in triage["reason"] or "respiratory" in triage["reason"].lower()


@pytest.mark.asyncio
async def test_parse_symptoms_api_negation(client: AsyncClient):
    payload = {"text": "Dog has hair loss on skin, no vomiting, not coughing."}
    response = await client.post("/api/v1/symptoms/parse", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert "hair_loss" in data["symptoms"]
    assert "vomiting" in data["negated_symptoms"]
    assert "coughing" in data["negated_symptoms"]
    assert "vomiting" not in data["symptoms"]


@pytest.mark.asyncio
async def test_parse_symptoms_api_swapped_trained_engine(client: AsyncClient):
    from app.features.symptom_nlp.infrastructure.ml.engine import TrainedNLPSymptomEngine
    from app.features.symptom_nlp.presentation.dependencies import (
        get_symptom_engine,
        set_symptom_engine_override,
    )
    from app.main import app
    from ml.nlp.pipeline import SymptomParserPipeline

    trained_engine = TrainedNLPSymptomEngine(pipeline=SymptomParserPipeline())
    app.dependency_overrides[get_symptom_engine] = lambda: trained_engine
    set_symptom_engine_override(trained_engine)

    try:
        payload = {"text": "Dog scratching left ear for three days, getting worse."}
        response = await client.post("/api/v1/symptoms/parse", json=payload)
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        data = body["data"]

        # Validate schema contract
        assert "scratching" in data["symptoms"]
        assert any(loc["part"] == "ear" for loc in data["body_locations"])
        assert data["duration"]["value"] == 3
        assert data["duration"]["unit"] == "days"
        assert "ear_inflammation" in data["condition_probabilities"]
        assert data["progression"] == "worsening"
        assert data["emergency_triage"]["is_critical"] is False
        assert data["model_version"] == trained_engine.get_version()
        assert len(data["spans"]) > 0
    finally:
        app.dependency_overrides.pop(get_symptom_engine, None)
        set_symptom_engine_override(None)

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_start_intake_session_api(client: AsyncClient):
    payload = {
        "dog_id": "dog_001",
        "initial_text": "My dog has been scratching his ear.",
    }
    response = await client.post("/api/v1/symptoms/intake/sessions", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["session_id"].startswith("intake_")
    assert data["dog_id"] == "dog_001"
    assert data["turn_count"] == 1
    assert "scratching" in data["current_parse"]["symptoms"]
    assert any(loc["part"] == "ear" for loc in data["current_parse"]["body_locations"])
    assert "body_location_side" in data["missing_slots"]
    assert "duration" in data["missing_slots"]
    assert data["is_complete"] is False
    assert len(data["agent_message"]) > 0


@pytest.mark.asyncio
async def test_start_intake_session_empty_text_fails(client: AsyncClient):
    payload = {
        "dog_id": "dog_001",
        "initial_text": "   ",
    }
    response = await client.post("/api/v1/symptoms/intake/sessions", json=payload)
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False


@pytest.mark.asyncio
async def test_conduct_intake_turn_api(client: AsyncClient):
    # 1. Start session
    start_payload = {
        "dog_id": "dog_001",
        "initial_text": "My dog is scratching its ear.",
    }
    start_res = await client.post("/api/v1/symptoms/intake/sessions", json=start_payload)
    assert start_res.status_code == 200
    session_id = start_res.json()["data"]["session_id"]

    # 2. Submit follow-up turn providing missing laterality and duration
    turn_payload = {
        "message": "It is the left ear, and it started 3 days ago. It is getting worse."
    }
    turn_res = await client.post(
        f"/api/v1/symptoms/intake/sessions/{session_id}/turns", json=turn_payload
    )
    assert turn_res.status_code == 200
    turn_data = turn_res.json()["data"]

    assert turn_data["turn_count"] == 2
    assert "scratching" in turn_data["current_parse"]["symptoms"]
    # Check that laterality and duration were resolved
    assert any(
        loc["part"] == "ear" and loc["side"] == "left"
        for loc in turn_data["current_parse"]["body_locations"]
    )
    assert turn_data["current_parse"]["duration"]["value"] == 3
    assert turn_data["current_parse"]["duration"]["unit"] == "days"
    assert turn_data["current_parse"]["progression"] == "worsening"
    # "body_location_side" and "duration" should no longer be missing
    assert "body_location_side" not in turn_data["missing_slots"]
    assert "duration" not in turn_data["missing_slots"]


@pytest.mark.asyncio
async def test_conduct_intake_turn_not_found(client: AsyncClient):
    res = await client.post(
        "/api/v1/symptoms/intake/sessions/intake_nonexistent123/turns",
        json={"message": "Left ear"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_clarifying_prompt_for_missing_symptoms(client: AsyncClient):
    payload = {
        "dog_id": "dog_002",
        "initial_text": "Something is wrong with my dog.",
    }
    response = await client.post("/api/v1/symptoms/intake/sessions", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "symptoms" in data["missing_slots"]
    assert (
        "physical signs" in data["agent_message"].lower()
        or "behavior" in data["agent_message"].lower()
    )


@pytest.mark.asyncio
async def test_turn_capping_at_max_turns(client: AsyncClient):
    # Turn 1
    res1 = await client.post(
        "/api/v1/symptoms/intake/sessions",
        json={"dog_id": "dog_003", "initial_text": "My dog seems uncomfortable."},
    )
    session_id = res1.json()["data"]["session_id"]

    # Turn 2
    res2 = await client.post(
        f"/api/v1/symptoms/intake/sessions/{session_id}/turns",
        json={"message": "He is not eating much."},
    )
    assert res2.json()["data"]["turn_count"] == 2

    # Turn 3
    res3 = await client.post(
        f"/api/v1/symptoms/intake/sessions/{session_id}/turns",
        json={"message": "Also sleeping a lot."},
    )
    assert res3.json()["data"]["turn_count"] == 3

    # Turn 4 (Capped)
    res4 = await client.post(
        f"/api/v1/symptoms/intake/sessions/{session_id}/turns",
        json={"message": "Started a few days ago."},
    )
    data4 = res4.json()["data"]
    assert data4["turn_count"] == 4
    assert (
        "consultation limit" in data4["agent_message"].lower()
        or "summarized" in data4["agent_message"].lower()
    )


@pytest.mark.asyncio
async def test_emergency_diversion_on_start(client: AsyncClient):
    payload = {
        "dog_id": "dog_004",
        "initial_text": "Help! My dog collapsed and has blue gums!",
    }
    response = await client.post("/api/v1/symptoms/intake/sessions", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "emergency_diverted"
    assert data["is_complete"] is True
    assert data["emergency_triage"]["is_critical"] is True
    assert "urgent medical alert" in data["agent_message"].lower()


@pytest.mark.asyncio
async def test_emergency_diversion_on_subsequent_turn(client: AsyncClient):
    # Start routine session
    start_res = await client.post(
        "/api/v1/symptoms/intake/sessions",
        json={"dog_id": "dog_005", "initial_text": "My dog is lethargic today."},
    )
    session_id = start_res.json()["data"]["session_id"]
    assert start_res.json()["data"]["status"] == "in_progress"

    # Turn 2: sudden emergency
    turn_res = await client.post(
        f"/api/v1/symptoms/intake/sessions/{session_id}/turns",
        json={"message": "Now he suddenly collapsed and is not responding!"},
    )
    assert turn_res.status_code == 200
    turn_data = turn_res.json()["data"]
    assert turn_data["status"] == "emergency_diverted"
    assert turn_data["is_complete"] is True
    assert turn_data["emergency_triage"]["is_critical"] is True

    # Turn 3: Attempting more turns when diverted should be rejected
    blocked_turn = await client.post(
        f"/api/v1/symptoms/intake/sessions/{session_id}/turns",
        json={"message": "What should I do?"},
    )
    assert blocked_turn.status_code == 400
    assert "already emergency_diverted" in blocked_turn.json()["error"]["message"]


@pytest.mark.asyncio
async def test_complete_intake_session_api(client: AsyncClient):
    # 1. Start consultation
    start_res = await client.post(
        "/api/v1/symptoms/intake/sessions",
        json={"dog_id": "dog_006", "initial_text": "Dog scratching right ear for two weeks."},
    )
    assert start_res.status_code == 200
    session_id = start_res.json()["data"]["session_id"]

    # 2. Finalize consultation
    complete_res = await client.post(f"/api/v1/symptoms/intake/sessions/{session_id}/complete")
    assert complete_res.status_code == 200
    body = complete_res.json()
    assert body["success"] is True
    evidence = body["data"]

    # Verify that returned evidence is full SymptomParseResponseData ready for Multimodal Fusion
    assert "scratching" in evidence["symptoms"]
    assert any(
        loc["part"] == "ear" and loc["side"] == "right" for loc in evidence["body_locations"]
    )
    assert evidence["duration"]["value"] == 2
    assert evidence["duration"]["unit"] == "weeks"
    assert "ear_inflammation" in evidence["condition_probabilities"]
    assert evidence["modality_reliability_score"] > 0.0
    assert evidence["text_quality_score"] > 0.0
    assert len(evidence["spans"]) > 0

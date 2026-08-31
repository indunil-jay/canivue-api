import pytest


@pytest.mark.asyncio
async def test_health_check_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_sample_crud_endpoints(client):
    # 1. Create
    payload = {"title": "API Sample", "description": "Created via API"}
    res = await client.post("/api/v1/samples", json=payload)
    assert res.status_code == 201
    res_data = res.json()
    assert res_data["success"] is True
    sample_id = res_data["data"]["id"]
    assert res_data["data"]["title"] == "API Sample"

    # 2. Get by ID
    get_res = await client.get(f"/api/v1/samples/{sample_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == sample_id

    # 3. List
    list_res = await client.get("/api/v1/samples")
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # 4. Update
    update_res = await client.put(
        f"/api/v1/samples/{sample_id}",
        json={"title": "Updated API Sample", "is_active": False},
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["title"] == "Updated API Sample"
    assert update_res.json()["data"]["is_active"] is False

    # 5. Delete
    delete_res = await client.delete(f"/api/v1/samples/{sample_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    # 6. Verify 404 after delete
    get_after_delete = await client.get(f"/api/v1/samples/{sample_id}")
    assert get_after_delete.status_code == 404

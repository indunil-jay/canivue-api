from tests.helpers import owner_headers

ME = "/api/v1/auth/me"
PRIVACY = "/api/v1/auth/me/privacy"


async def test_profile_starts_without_contact_details(client):
    headers = await owner_headers(client, full_name="Alex Taylor")

    me = (await client.get(ME, headers=headers)).json()["data"]

    assert me["full_name"] == "Alex Taylor"
    assert me["phone"] is None
    assert me["address"] is None
    assert me["emergency_contact"] is None


async def test_user_can_update_personal_information(client):
    headers = await owner_headers(client, full_name="Alex Taylor")

    resp = await client.patch(
        ME,
        headers=headers,
        json={"full_name": "Alex T.", "phone": "+1 555 234 5678", "address": "San Francisco, CA"},
    )

    assert resp.status_code == 200
    me = (await client.get(ME, headers=headers)).json()["data"]
    assert me["full_name"] == "Alex T."
    assert me["phone"] == "+1 555 234 5678"
    assert me["address"] == "San Francisco, CA"


async def test_partial_update_leaves_other_fields_alone(client):
    headers = await owner_headers(client, full_name="Alex Taylor")
    await client.patch(ME, headers=headers, json={"phone": "111"})

    await client.patch(ME, headers=headers, json={"emergency_contact": "Sam 222"})

    me = (await client.get(ME, headers=headers)).json()["data"]
    assert me["full_name"] == "Alex Taylor"
    assert me["phone"] == "111"
    assert me["emergency_contact"] == "Sam 222"


async def test_profile_update_requires_authentication(client):
    assert (await client.patch(ME, json={"phone": "111"})).status_code == 401


async def test_privacy_settings_have_safe_defaults(client):
    headers = await owner_headers(client)

    resp = await client.get(PRIVACY, headers=headers)

    assert resp.status_code == 200
    assert resp.json()["data"] == {
        "share_with_vet": True,
        "share_anonymized_research": False,
        "location_services": False,
        "two_factor_enabled": False,
    }


async def test_user_can_change_privacy_settings(client):
    headers = await owner_headers(client)

    resp = await client.patch(
        PRIVACY, headers=headers, json={"share_with_vet": False, "location_services": True}
    )

    assert resp.status_code == 200
    saved = (await client.get(PRIVACY, headers=headers)).json()["data"]
    assert saved["share_with_vet"] is False
    assert saved["location_services"] is True
    assert saved["share_anonymized_research"] is False


async def test_privacy_settings_are_per_user(client):
    first = await owner_headers(client, "first@example.com")
    second = await owner_headers(client, "second@example.com")

    await client.patch(PRIVACY, headers=first, json={"share_with_vet": False})

    assert (await client.get(PRIVACY, headers=second)).json()["data"]["share_with_vet"] is True

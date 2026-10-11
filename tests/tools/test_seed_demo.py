from tests.helpers import login_headers
from tools.seed_demo import ADMIN_EMAIL, DEMO_PASSWORD, OWNER_EMAIL, VETS, seed_demo

API = "/api/v1"


async def test_demo_seed_gives_the_owner_a_usable_account(client, db_session):
    assert await seed_demo(db_session) is True
    owner = await login_headers(client, OWNER_EMAIL, DEMO_PASSWORD)

    dogs = (await client.get(f"{API}/dogs", headers=owner)).json()["data"]
    vets = (await client.get(f"{API}/veterinarians", headers=owner)).json()["data"]
    buddy = next(d for d in dogs if d["name"] == "Buddy")
    base = f"{API}/dogs/{buddy['id']}"
    dashboard = (await client.get(f"{base}/dashboard", headers=owner)).json()["data"]
    series = (await client.get(f"{base}/metrics/heartRate", headers=owner)).json()["data"]
    insights = (await client.get(f"{base}/insights", headers=owner)).json()["data"]
    feed = (await client.get(f"{API}/community/feed", headers=owner)).json()["data"]

    assert sorted(d["name"] for d in dogs) == ["Buddy", "Charlie", "Luna"]
    assert sorted(v["name"] for v in vets) == sorted(v[1] for v in VETS)
    assert all(v["verified"] for v in vets)
    assert dashboard["health_score"] is not None
    assert dashboard["vitals"]["heart_rate_bpm"] is not None
    assert dashboard["device"]["state"] == "connected"
    assert dashboard["appointment"]["vet_name"] == "Dr. Sarah Jenkins"
    assert len(dashboard["reminders"]) == 3
    assert len(series["points"]) >= 6
    assert insights
    assert len(feed) == 2


async def test_demo_seed_does_nothing_the_second_time(client, db_session):
    await seed_demo(db_session)

    assert await seed_demo(db_session) is False

    owner = await login_headers(client, OWNER_EMAIL, DEMO_PASSWORD)
    assert len((await client.get(f"{API}/dogs", headers=owner)).json()["data"]) == 3


async def test_demo_veterinarian_and_admin_can_sign_in(client, db_session):
    await seed_demo(db_session)

    vet = await login_headers(client, VETS[0][0], DEMO_PASSWORD)
    admin = await login_headers(client, ADMIN_EMAIL, DEMO_PASSWORD)

    patients = (await client.get(f"{API}/vet-portal/patients", headers=vet)).json()["data"]
    pending = await client.get(f"{API}/veterinarians/pending", headers=admin)
    assert [p["dog_name"] for p in patients] == ["Buddy"]
    assert pending.status_code == 200

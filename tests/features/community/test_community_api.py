import pytest

from app.features.community.infrastructure.persistence.seed import seed_communities
from tests.helpers import owner_headers, vet_headers

COMMUNITY = "/api/v1/community"


@pytest.fixture
async def alice(client, db_session):
    await seed_communities(db_session)
    return await owner_headers(client, "alice@example.com", full_name="Alice Perera")


@pytest.fixture
async def bob(client, alice):
    return await owner_headers(client, "bob@example.com", full_name="Bob Silva")


async def _post(client, headers, content="Any tips for itchy paws?", community="skin-allergies"):
    resp = await client.post(
        f"{COMMUNITY}/posts", headers=headers, json={"community_id": community, "content": content}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _feed(client, headers, **params) -> list[dict]:
    resp = await client.get(f"{COMMUNITY}/feed", headers=headers, params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _communities(client, headers) -> dict[str, dict]:
    resp = await client.get(f"{COMMUNITY}/communities", headers=headers)
    return {c["id"]: c for c in resp.json()["data"]}


async def test_default_communities_exist_with_no_members(client, alice):
    communities = await _communities(client, alice)

    assert sorted(c["name"] for c in communities.values()) == [
        "Arthritis", "Diabetes", "Digestive Problems", "Heart Conditions", "Obesity",
        "Skin Allergies",
    ]  # fmt: skip
    assert all(c["member_count"] == 0 and c["joined"] is False for c in communities.values())


async def test_seeding_twice_does_not_duplicate(client, alice, db_session):
    await seed_communities(db_session)

    assert len(await _communities(client, alice)) == 6


async def test_user_publishes_a_post(client, alice):
    post = await _post(client, alice)

    assert post["author_name"] == "Alice Perera"
    assert post["author_initials"] == "AP"
    assert post["is_veterinarian"] is False
    assert post["community_tag"] == "Skin Allergies"
    assert post["content"] == "Any tips for itchy paws?"
    assert (post["like_count"], post["comment_count"], post["share_count"]) == (0, 0, 0)
    assert (post["liked_by_me"], post["saved_by_me"]) == (False, False)


async def test_posts_by_veterinarians_are_flagged(client, alice):
    vet = await vet_headers(client, "vet@example.com", full_name="Dr. Sarah Jenkins")

    post = await _post(client, vet, "Omega-3 can help with dry skin.")

    assert post["is_veterinarian"] is True
    assert (await _feed(client, alice))[0]["is_veterinarian"] is True


async def test_feed_is_newest_first_and_filterable_by_community(client, alice):
    await _post(client, alice, "First", "skin-allergies")
    await _post(client, alice, "Second", "arthritis")
    await _post(client, alice, "Third", "skin-allergies")

    assert [p["content"] for p in await _feed(client, alice)] == ["Third", "Second", "First"]
    skin = await _feed(client, alice, community_id="skin-allergies")
    assert [p["content"] for p in skin] == ["Third", "First"]


async def test_posting_to_an_unknown_community_is_rejected(client, alice):
    resp = await client.post(
        f"{COMMUNITY}/posts", headers=alice, json={"community_id": "cats", "content": "Hi"}
    )

    assert resp.status_code == 404


async def test_likes_toggle_per_user_and_count_across_users(client, alice, bob):
    post = await _post(client, alice)
    url = f"{COMMUNITY}/posts/{post['id']}/like"

    by_alice = (await client.post(url, headers=alice)).json()["data"]
    by_bob = (await client.post(url, headers=bob)).json()["data"]

    assert (by_alice["like_count"], by_alice["liked_by_me"]) == (1, True)
    assert (by_bob["like_count"], by_bob["liked_by_me"]) == (2, True)

    unliked = (await client.post(url, headers=alice)).json()["data"]

    assert (unliked["like_count"], unliked["liked_by_me"]) == (1, False)
    assert (await _feed(client, bob))[0]["liked_by_me"] is True
    assert (await _feed(client, alice))[0]["liked_by_me"] is False


async def test_saved_posts_are_private_to_the_saver(client, alice, bob):
    kept = await _post(client, alice, "Keep this")
    await _post(client, alice, "Not this")

    saved = (await client.post(f"{COMMUNITY}/posts/{kept['id']}/save", headers=bob)).json()["data"]

    assert saved["saved_by_me"] is True
    assert saved["like_count"] == 0
    assert [p["content"] for p in await _feed(client, bob, saved=True)] == ["Keep this"]
    assert await _feed(client, alice, saved=True) == []

    await client.post(f"{COMMUNITY}/posts/{kept['id']}/save", headers=bob)

    assert await _feed(client, bob, saved=True) == []


async def test_sharing_increments_the_share_count(client, alice, bob):
    post = await _post(client, alice)
    url = f"{COMMUNITY}/posts/{post['id']}/share"

    await client.post(url, headers=alice)
    shared = (await client.post(url, headers=bob)).json()["data"]

    assert shared["share_count"] == 2


async def test_joining_and_leaving_a_community_updates_member_counts(client, alice, bob):
    url = f"{COMMUNITY}/communities/arthritis/join"

    await client.post(url, headers=alice)
    joined = (await client.post(url, headers=bob)).json()["data"]

    assert (joined["member_count"], joined["joined"]) == (2, True)
    assert (await _communities(client, alice))["arthritis"]["joined"] is True
    assert (await _communities(client, alice))["diabetes"]["member_count"] == 0

    left = (await client.post(url, headers=alice)).json()["data"]

    assert (left["member_count"], left["joined"]) == (1, False)


async def test_unknown_posts_and_communities_are_not_found(client, alice):
    assert (await client.post(f"{COMMUNITY}/posts/nope/like", headers=alice)).status_code == 404
    assert (await client.post(f"{COMMUNITY}/posts/nope/share", headers=alice)).status_code == 404
    join = await client.post(f"{COMMUNITY}/communities/nope/join", headers=alice)
    assert join.status_code == 404


async def test_community_requires_authentication(client):
    assert (await client.get(f"{COMMUNITY}/feed")).status_code == 401

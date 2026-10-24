"""Content-hash cache: hits, invalidation by content, separation by user and mode."""

from conftest import SpyLLM

from hacktx_app.dev.fixtures import ALEX
from hacktx_app.services.cache import TTLCache

IDEA = {"mode": "elaborate_idea", "idea": "plant watering robot"}


def post(client, user_id="fixture-ece", body=IDEA):
    response = client.post(f"/api/users/{user_id}/chat", json=body)
    assert response.status_code == 200, response.json
    return response.json


def test_identical_request_hits_cache(client, spy):
    first, second = post(client), post(client)
    assert len(spy.calls) == 1
    assert first["cache_hit"] is False and second["cache_hit"] is True
    assert first["project"] == second["project"]


def test_profile_change_invalidates_by_content(client, spy, data):
    post(client)
    data.replace_user(ALEX.model_copy(update={"interests": ("robots",)}))
    post(client)
    assert len(spy.calls) == 2


def test_preferences_and_idea_change_the_key(client, spy):
    post(client)
    post(client, body={**IDEA, "preferences": {"skill_level": "beginner"}})
    post(client, body={**IDEA, "idea": "a different idea"})
    assert len(spy.calls) == 3


def test_different_users_never_share_entries(client, spy):
    a, b = post(client, "fixture-ece"), post(client, "fixture-cs")
    assert len(spy.calls) == 2
    assert a["user_id"] == "fixture-ece" and b["user_id"] == "fixture-cs"


def test_mock_and_real_modes_never_share_entries(make_client, data):
    # Same cache-relevant content, different provider mode -> different keys.
    spy_mock, spy_real = SpyLLM(mode="mock"), SpyLLM(mode="anthropic", model_id="claude-opus-5-5")
    app_client = make_client(data_provider=data, llm_provider=spy_mock)
    post(app_client)
    ctx = app_client.application.extensions["hacktx_app"]
    ctx.llm_provider = spy_real
    body = post(app_client)
    assert body["cache_hit"] is False and len(spy_real.calls) == 1


def test_invalid_output_is_not_cached(make_client, data):
    from test_generation import InventingLLM

    llm = InventingLLM()
    client = make_client(data_provider=data, llm_provider=llm)
    assert client.post("/api/users/fixture-ece/chat", json=IDEA).status_code == 502
    assert len(client.application.extensions["hacktx_app"].cache) == 0


def test_ttl_expiry_and_size_bound():
    now = [0.0]
    cache = TTLCache(max_entries=2, ttl_seconds=10, clock=lambda: now[0])
    cache.set("a", {"v": 1})
    cache.set("b", {"v": 2})
    cache.set("c", {"v": 3})
    assert cache.get("a") is None and len(cache) == 2
    now[0] = 11
    assert cache.get("b") is None


def test_cached_values_are_copies():
    cache = TTLCache()
    cache.set("k", {"list": [1]})
    cache.get("k")["list"].append(2)
    assert cache.get("k") == {"list": [1]}

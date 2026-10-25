"""SerpApi payload conversions and the cached client (httpx mock transport, no network)."""

import json

import httpx
import pytest
from fake_search import GOOGLE, SCHOLAR, SHOPPING, YOUTUBE

import db
from json_api.search import DisabledSearch, SearchError, offers_from, resources_from
from serp import CacheOnlySearch, SerpApiClient, cache_size, export_cache, import_cache


def test_youtube_results_become_tutorials_and_skip_bad_or_duplicate_links():
    found = resources_from("youtube", YOUTUBE, id_prefix="7", tags=("sensors",))
    assert [r.url for r in found] == [
        "https://www.youtube.com/watch?v=fake0001",
        "https://www.youtube.com/watch?v=fake0002",
    ]
    first = found[0]
    assert first.kind == "tutorial" and first.provider == "YouTube"
    assert first.source == "serpapi:youtube" and first.verification_status == "provided_unverified"
    assert first.thumbnail_url.endswith("hqdefault.jpg")
    assert first.metadata["channel"] == "Maker Channel" and first.metadata["length"] == "12:34"
    assert first.id.startswith("7/youtube-") and first.topic_tags == ("sensors",)


def test_scholar_results_become_research_with_metadata():
    found = resources_from("google_scholar", SCHOLAR, id_prefix="web")
    assert len(found) == 1
    paper = found[0]
    assert paper.kind == "research" and paper.provider == "Google Scholar"
    assert paper.metadata == {"summary": "A Author, B Author - Sensors, 2021", "cited_by": "42"}
    assert paper.content_excerpt.startswith("We review")


def test_google_results_become_documentation_and_limit_applies():
    found = resources_from("google", GOOGLE, id_prefix="web", limit=1)
    assert len(found) == 1 and found[0].kind == "documentation"
    assert found[0].provider == "Example Docs"
    with pytest.raises(ValueError):
        resources_from("google_shopping", SHOPPING, id_prefix="web")


def test_shopping_offers():
    offers = offers_from(SHOPPING)
    assert offers == [
        {
            "title": "Capacitive Soil Moisture Sensor v1.2 (3 pack)",
            "url": "https://shop.example.com/soil-sensor",
            "price_usd": 8.99,
            "source": "Example Shop",
            "thumbnail_url": "https://shop.example.com/soil.jpg",
        }
    ]
    assert offers_from({}) == []


def test_disabled_search_fails_loudly():
    assert DisabledSearch().enabled is False
    with pytest.raises(SearchError, match="SERPAPI_API_KEY"):
        DisabledSearch().search("google", "anything")


# ---- the client ----------------------------------------------------------------------------


def make_client(conn, responses, max_searches=None):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        engine = request.url.params["engine"]
        status, body = responses[engine]
        return httpx.Response(status, json=body)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    client = SerpApiClient("test-key", lambda: conn, max_searches=max_searches, http=http)
    return client, seen


def test_client_caches_each_query_once():
    conn = db.connect_memory(seed=False)
    client, seen = make_client(conn, {"youtube": (200, YOUTUBE)})
    first = client.search("youtube", "  soil   moisture tutorial ")
    again = client.search("youtube", "soil moisture tutorial")
    assert first == again == YOUTUBE
    assert len(seen) == 1 and client.calls == 1 and cache_size(conn) == 1
    assert seen[0].url.params["search_query"] == "soil moisture tutorial"
    assert seen[0].url.params["api_key"] == "test-key"
    assert client.cached("youtube", "soil moisture tutorial") == YOUTUBE
    assert client.cached("youtube", "something else") is None


def test_client_respects_the_search_budget_but_still_serves_the_cache():
    conn = db.connect_memory(seed=False)
    client, _ = make_client(conn, {"google": (200, GOOGLE), "youtube": (200, YOUTUBE)}, 1)
    client.search("google", "one")
    with pytest.raises(SearchError, match="budget"):
        client.search("youtube", "two")
    assert client.search("google", "one") == GOOGLE  # cached, free


def test_client_surfaces_serpapi_errors_without_caching_them():
    conn = db.connect_memory(seed=False)
    client, _ = make_client(
        conn,
        {
            "google_scholar": (200, {"error": "Your account has run out of searches."}),
            "youtube": (401, {"error": "Invalid API key"}),
        },
    )
    with pytest.raises(SearchError, match="run out of searches"):
        client.search("google_scholar", "nothing")
    with pytest.raises(SearchError, match="HTTP 401"):
        client.search("youtube", "nothing")
    assert cache_size(conn) == 0
    with pytest.raises(SearchError, match="Unknown search engine"):
        client.search("bing", "nothing")


def test_no_results_is_a_valid_cached_answer_not_an_error():
    conn = db.connect_memory(seed=False)
    empty = {"error": "Youtube hasn't returned any results for this query."}
    client, seen = make_client(conn, {"youtube": (200, empty)})
    assert client.search("youtube", "a very long sentence nobody filmed") == empty
    assert resources_from("youtube", empty, id_prefix="web") == []
    client.search("youtube", "a very long sentence nobody filmed")
    assert len(seen) == 1 and cache_size(conn) == 1  # cached, not retried


def test_cached_payload_round_trips_as_json():
    conn = db.connect_memory(seed=False)
    client, _ = make_client(conn, {"google_scholar": (200, SCHOLAR)})
    client.search("google_scholar", "soil")
    row = conn.execute("SELECT response_json FROM serp_cache").fetchone()
    assert json.loads(row[0]) == SCHOLAR


# ---- offline replay: export, import, cache-only search --------------------------------------


def test_export_trims_and_import_restores_the_cache(tmp_path):
    conn = db.connect_memory(seed=False)
    fat_youtube = {**YOUTUBE, "search_metadata": {"id": "x" * 500}, "search_parameters": {}}
    client, _ = make_client(conn, {"youtube": (200, fat_youtube), "google": (200, GOOGLE)})
    client.search("youtube", "soil tutorial")
    client.search("google", "soil guide")
    path = tmp_path / "serp_cache.json"
    assert export_cache(conn, path) == 2
    entries = json.loads(path.read_text(encoding="utf-8"))
    youtube = next(e for e in entries if e["engine"] == "youtube")
    assert "search_metadata" not in youtube["response"]
    assert len(youtube["response"]["video_results"]) == len(YOUTUBE["video_results"])
    # The trimmed payload converts exactly like the full one.
    assert [r.url for r in resources_from("youtube", youtube["response"], id_prefix="w")] == [
        r.url for r in resources_from("youtube", YOUTUBE, id_prefix="w")
    ]

    fresh = db.connect_memory(seed=False)
    assert import_cache(fresh, path) == 2 and cache_size(fresh) == 2
    cache_only = CacheOnlySearch(lambda: fresh)
    assert cache_only.search("google", " soil  guide ") == {
        "organic_results": GOOGLE["organic_results"]
    }
    with pytest.raises(SearchError, match="offline cache"):
        cache_only.search("google", "never searched")


def test_seeding_replays_the_snapshot_into_resources_and_shop_links(tmp_path, monkeypatch):
    import seeding
    from json_api.search import project_queries
    from sqlite_provider import SQLiteProjectDataProvider

    # Build a snapshot for project 7 (Smart Soil Moisture Monitor) from the canned payloads.
    scratch = db.connect_memory()
    project = SQLiteProjectDataProvider(lambda: scratch).get_project("7")
    queries = project_queries(project)
    for engine, payload in (("youtube", YOUTUBE), ("google", GOOGLE)):
        scratch.execute(
            "INSERT INTO serp_cache (engine, query, response_json) VALUES (?, ?, ?)",
            (engine, queries[engine], json.dumps(payload)),
        )
    first_material = project.materials[0].name
    scratch.execute(
        "INSERT INTO serp_cache (engine, query, response_json) VALUES (?, ?, ?)",
        ("google_shopping", first_material, json.dumps(SHOPPING)),
    )
    snapshot = tmp_path / "serp_cache.json"
    export_cache(scratch, snapshot)

    monkeypatch.setattr(seeding, "CACHE_SNAPSHOT", snapshot)
    conn = db.connect_memory(replay=True)  # seeds, then replays the snapshot (as app.py does)
    rebuilt = SQLiteProjectDataProvider(lambda: conn).get_project("7")
    found = [r for r in rebuilt.resources if r.source != "authored"]
    assert sorted(r.source for r in found) == [
        "serpapi:google",
        "serpapi:youtube",
        "serpapi:youtube",
    ]
    assert rebuilt.materials[0].shop_url == "https://shop.example.com/soil-sensor"
    assert (
        rebuilt.materials[0].price_usd == 8.99
        and rebuilt.materials[0].shop_source == "Example Shop"
    )
    # Other projects are untouched, and a second start changes nothing.
    assert all(
        r.source == "authored"
        for r in SQLiteProjectDataProvider(lambda: conn).get_project("1").resources
    )
    before = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
    db.apply_schema(conn)
    assert conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0] == before


def test_client_reports_the_account_balance_without_spending_a_search():
    conn = db.connect_memory(seed=False)
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.url.path == "/account.json" and request.url.params["api_key"] == "k"
        return httpx.Response(
            200, json={"plan_searches_left": 89, "extra_credits": 1000, "this_month_usage": 161}
        )

    http = httpx.Client(transport=httpx.MockTransport(handler))
    client = SerpApiClient("k", lambda: conn, http=http)
    assert client.account() == {"searches_left": 1089, "plan_searches_left": 89, "used": 161}
    assert client.calls == 0 and len(seen) == 1


def test_account_balance_failure_is_a_search_error():
    conn = db.connect_memory(seed=False)
    http = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401, json={})))
    with pytest.raises(SearchError, match="HTTP 401"):
        SerpApiClient("k", lambda: conn, http=http).account()

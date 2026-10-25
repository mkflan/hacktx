"""SerpApi payload conversions and the cached client (httpx mock transport, no network)."""

import json

import httpx
import pytest
from fake_search import GOOGLE, SCHOLAR, SHOPPING, YOUTUBE

import db
from json_api.search import DisabledSearch, SearchError, offers_from, resources_from
from serp import SerpApiClient, cache_size


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

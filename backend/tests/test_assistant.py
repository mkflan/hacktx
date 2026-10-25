"""The Caterpillar: chat replies, source discipline and the starter, with the mock LLM and a
fake search provider. No network, no paid calls."""

import pytest
from fake_search import FakeSearch

import db
from json_api.config import Settings
from json_api.llm.mock import MockLLMProvider
from json_api.search import SearchError
from json_api.services.assistant import REMOVED_LINK, strip_unknown_urls
from sqlite_provider import SQLiteProjectDataProvider

SETTINGS = Settings(data_mode="injected")


class InventingLLM(MockLLMProvider):
    """A model that makes up a link: the service must remove it."""

    def chat(self, system, turns):
        return (
            "Try this guide: https://made-up.example.com/guide. "
            "Also see https://docs.arduino.cc/learn/starting-guide/getting-started-arduino/ ."
        )


@pytest.fixture
def conn():
    connection = db.connect_memory()
    yield connection
    connection.close()


@pytest.fixture
def search():
    return FakeSearch()


@pytest.fixture
def client(make_client, conn, search):
    return make_client(
        data_provider=SQLiteProjectDataProvider(lambda: conn),
        llm_provider=MockLLMProvider(),
        search_provider=search,
        settings_override=SETTINGS,
    )


def ask(client, user="1", **body):
    body.setdefault("messages", [{"role": "user", "content": "Where do I start?"}])
    return client.post(f"/api/users/{user}/assistant", json=body)


def test_strip_unknown_urls_keeps_allowed_and_trailing_punctuation():
    text = "See https://ok.example.com/a, then https://bad.example.com/b. Done (https://ok.example.com/a)."
    cleaned, removed = strip_unknown_urls(text, {"https://ok.example.com/a"})
    assert removed == 1
    assert (
        cleaned
        == f"See https://ok.example.com/a, then {REMOVED_LINK}. Done (https://ok.example.com/a)."
    )


def test_project_mode_reply_knows_the_project_and_cites_only_its_sources(client):
    response = ask(client, project_id="7")  # Smart Soil Moisture Monitor
    assert response.status_code == 200
    body = response.json
    assert body["mode"] == "project" and body["project_id"] == "7"
    assert "Smart Soil Moisture Monitor" in body["reply"]
    assert body["generation_mode"] == "mock" and body["persisted"] is False
    assert {w["code"] for w in body["warnings"]} == {"MOCK_GENERATION"}
    assert body["web_results"] == []
    cited = {r["url"] for r in body["cited_sources"]}
    assert cited and cited <= {
        "https://docs.arduino.cc/learn/starting-guide/getting-started-arduino/",
        "https://www.arduino.cc/reference/en/language/functions/analog-io/analogread/",
    }


def test_general_mode_reply_offers_the_starter(client):
    response = ask(client, messages=[{"role": "user", "content": "An app that waters my plants"}])
    assert response.status_code == 200
    body = response.json
    assert body["mode"] == "general" and body["project_id"] is None
    assert "Turn into a project starter" in body["reply"]


def test_dig_deeper_runs_a_live_search_and_returns_labeled_results(client, search):
    response = ask(client, project_id="7", dig_deeper=True)
    body = response.json
    assert [engine for engine, _ in search.calls] == ["youtube", "google"]
    assert "Smart Soil Moisture Monitor" in search.calls[0][1]
    assert [r["source"] for r in body["web_results"]] == [
        "serpapi:youtube",
        "serpapi:youtube",
        "serpapi:google",
    ]
    assert all(r["verification_status"] == "provided_unverified" for r in body["web_results"])


def test_dig_deeper_without_search_configured_is_an_honest_notice(make_client, conn):
    client = make_client(
        data_provider=SQLiteProjectDataProvider(lambda: conn),
        llm_provider=MockLLMProvider(),
        settings_override=SETTINGS,
    )
    body = ask(client, dig_deeper=True).json
    assert body["web_results"] == []
    assert "SEARCH_UNAVAILABLE" in {w["code"] for w in body["warnings"]}


def test_search_failure_still_answers(make_client, conn):
    client = make_client(
        data_provider=SQLiteProjectDataProvider(lambda: conn),
        llm_provider=MockLLMProvider(),
        search_provider=FakeSearch(fail=SearchError("quota spent")),
        settings_override=SETTINGS,
    )
    response = ask(client, dig_deeper=True)
    assert response.status_code == 200
    codes = {w["code"] for w in response.json["warnings"]}
    assert "SEARCH_FAILED" in codes


def test_one_failing_engine_does_not_lose_the_others(make_client, conn):
    search = FakeSearch(fail=SearchError("no results"), fail_engines={"youtube"})
    client = make_client(
        data_provider=SQLiteProjectDataProvider(lambda: conn),
        llm_provider=MockLLMProvider(),
        search_provider=search,
        settings_override=SETTINGS,
    )
    body = ask(client, project_id="7", dig_deeper=True).json
    assert [r["source"] for r in body["web_results"]] == ["serpapi:google"]
    failed = [w for w in body["warnings"] if w["code"] == "SEARCH_FAILED"]
    assert len(failed) == 1 and "youtube" in failed[0]["message"]
    # YouTube gets a short query; Google the full sentence with the project name.
    queries = dict(search.calls)
    assert queries["youtube"].startswith("Smart Soil Moisture Monitor")
    assert len(queries["youtube"].split()) <= 12
    assert queries["google"].endswith("Where do I start?")


def test_invented_links_are_removed_and_reported(make_client, conn):
    client = make_client(
        data_provider=SQLiteProjectDataProvider(lambda: conn),
        llm_provider=InventingLLM(),
        settings_override=SETTINGS,
    )
    body = ask(client, project_id="7").json
    assert "made-up.example.com" not in body["reply"]
    assert REMOVED_LINK in body["reply"]
    assert "docs.arduino.cc" in body["reply"]  # a real project source survives
    assert any(w["code"] == "LINKS_REMOVED" for w in body["warnings"])
    assert [r["url"] for r in body["cited_sources"]] == [
        "https://docs.arduino.cc/learn/starting-guide/getting-started-arduino/"
    ]


@pytest.mark.parametrize(
    ("body", "status"),
    [
        ({"messages": []}, 422),
        ({"messages": [{"role": "system", "content": "x"}]}, 422),
        ({"messages": [{"role": "user", "content": "x"}], "project_id": "999"}, 404),
        ({"messages": [{"role": "user", "content": "x"}], "extra": 1}, 422),
    ],
)
def test_bad_requests(client, body, status):
    assert client.post("/api/users/1/assistant", json=body).status_code == status
    assert ask(client, user="999").status_code == 404


def test_starter_builds_a_plan_with_web_sources_first(client, search):
    response = client.post(
        "/api/users/2/starter",
        json={
            "idea": "A web app that quizzes me on Spanish verbs from my chat history",
            "conversation": [
                {"role": "user", "content": "A web app that quizzes me on Spanish verbs"},
                {"role": "assistant", "content": "What should the demo show?"},
                {"role": "user", "content": "A daily quiz with a streak counter"},
            ],
        },
    )
    assert response.status_code == 200
    body = response.json
    assert body["mode"] == "starter" and body["persisted"] is False
    assert [engine for engine, _ in search.calls] == ["youtube", "google_scholar"]
    plan = body["project"]
    assert plan["name"] and len(plan["milestones"]) >= 4
    web_urls = {r["url"] for r in body["web_results"]}
    assert web_urls == {
        "https://www.youtube.com/watch?v=fake0001",
        "https://www.youtube.com/watch?v=fake0002",
        "https://example.org/paper/soil-review",
    }
    # The mock cites the first bank items, which are the live web results.
    assert {r["url"] for r in plan["resources"]} & web_urls
    assert [r["url"] for r in plan["research_connections"]] == [
        "https://example.org/paper/soil-review"
    ]
    assert body["original_idea"].startswith("A web app that quizzes me")
    assert "Notes from the mentoring conversation" in body["original_idea"]


def test_starter_without_search_still_plans_from_the_catalog(make_client, conn):
    client = make_client(
        data_provider=SQLiteProjectDataProvider(lambda: conn),
        llm_provider=MockLLMProvider(),
        settings_override=SETTINGS,
    )
    body = client.post("/api/users/2/starter", json={"idea": "vocabulary flashcards app"}).json
    assert body["web_results"] == []
    assert "SEARCH_UNAVAILABLE" in {w["code"] for w in body["warnings"]}
    assert body["project"]["milestones"]

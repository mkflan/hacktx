"""Chat page, live "Dig deeper" on a project, and posting a starter to Wonderland. In-memory
SQLite, mock LLM, fake search; StrictUndefined catches missing template variables."""

import json

import pytest
from fake_search import FakeSearch
from jinja2 import StrictUndefined

import app as flask_app
import db
from json_api.config import Settings
from json_api.llm.mock import MockLLMProvider
from sqlite_provider import SQLiteProjectDataProvider


def make_client(conn, search=None):
    app = flask_app.create_app(
        settings=Settings(data_mode="injected"),
        config={"DATABASE": ":memory:", "TESTING": True},
        data_provider=SQLiteProjectDataProvider(lambda: conn),
        llm_provider=MockLLMProvider(),
    )
    if search is not None:
        from json_api.dependencies import get_context

        with app.app_context():
            get_context().search_provider = search
    app.jinja_env.undefined = StrictUndefined
    return app.test_client()


@pytest.fixture
def conn(monkeypatch):
    connection = db.connect_memory()
    monkeypatch.setattr(db, "get_db", lambda: connection)
    yield connection
    connection.close()


@pytest.fixture
def client(conn):
    return make_client(conn)


@pytest.fixture
def searching_client(conn):
    return make_client(conn, FakeSearch())


def test_chat_needs_a_profile(client):
    response = client.get("/chat")
    assert response.status_code == 302 and response.headers["Location"].endswith("/?new=1")


def test_chat_general_mode(client):
    client.post("/session/2")
    page = client.get("/chat").get_data(as_text=True)
    assert "Ask the Caterpillar" in page and "maya_demo" in page
    assert 'id="starterBtn"' in page
    assert "Dig deeper on the web (unavailable)" in page  # no search provider in this app


def test_chat_project_mode(client, searching_client):
    client.post("/session/1")
    page = client.get("/chat?project=7").get_data(as_text=True)
    assert "Smart Soil Moisture Monitor" in page and "The Caterpillar knows" in page
    assert 'id="starterBtn"' not in page
    assert client.get("/chat?project=999").status_code == 404
    searching_client.post("/session/1")
    assert "(unavailable)" not in searching_client.get("/chat").get_data(as_text=True)


def test_dig_deeper_stores_results_on_the_project(client, searching_client, conn):
    assert client.post("/projects/7/dig").status_code == 503
    assert client.post("/projects/7/dig").json["error"]["code"] == "SEARCH_UNAVAILABLE"

    response = searching_client.post("/projects/7/dig")
    assert response.status_code == 200
    body = response.json
    assert body["new"] == 3 and body["cache_hit"] is False
    assert [r["source"] for r in body["results"]] == [
        "serpapi:youtube",
        "serpapi:youtube",
        "serpapi:google",
    ]
    rows = conn.execute(
        "SELECT source, kind FROM resources WHERE project_id = 7 AND source != 'authored'"
    ).fetchall()
    assert sorted((r["source"], r["kind"]) for r in rows) == [
        ("serpapi:google", "documentation"),
        ("serpapi:youtube", "tutorial"),
        ("serpapi:youtube", "tutorial"),
    ]

    page = searching_client.get("/projects/7").get_data(as_text=True)
    assert "Build a soil moisture sensor with Arduino" in page
    assert "found via SerpApi youtube" in page
    assert "hqdefault.jpg" in page  # thumbnail

    again = searching_client.post("/projects/7/dig").json
    assert again["new"] == 0 and again["cache_hit"] is True
    assert searching_client.post("/projects/999/dig").status_code == 404


def test_starter_can_be_posted_to_wonderland_and_read(searching_client):
    client = searching_client
    client.post("/session/2")
    starter = client.post(
        "/api/users/2/starter",
        json={"idea": "A Spanish verb quiz web app with a streak counter"},
    ).json
    payload = {
        "plan": starter["project"],
        "original_idea": starter["original_idea"],
        "generation_mode": starter["generation_mode"],
        "web_results": starter["web_results"],
    }
    response = client.post("/forum/starters", data={"plan_json": json.dumps(payload)})
    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/forum/posts/" in location

    page = client.get(location).get_data(as_text=True)
    assert starter["project"]["name"] in page
    assert "Milestones" in page and "Project starter by maya_demo" in page
    assert "Sources dug up for this idea with SerpApi" in page
    assert "https://www.youtube.com/watch?v=fake0001" in page

    forum_page = client.get("/forum").get_data(as_text=True)
    assert "Project starter" in forum_page and starter["project"]["name"] in forum_page
    only_starters = client.get("/forum?kind=starter").get_data(as_text=True)
    assert "Soil sensor readings are noisy" not in only_starters
    assert starter["project"]["name"] in only_starters
    assert "Soil sensor readings are noisy" in client.get("/forum?q=noisy").get_data(as_text=True)
    assert client.get("/forum?sort=hours&difficulty=beginner").status_code == 200
    assert client.get("/forum/posts/999").status_code == 404


def test_posting_a_starter_needs_a_profile_and_valid_json(client):
    assert client.post("/forum/starters", data={"plan_json": "{}"}).status_code == 400
    client.post("/session/1")
    assert client.post("/forum/starters", data={"plan_json": "not json"}).status_code == 400
    assert client.post("/forum/starters", data={"plan_json": "{}"}).status_code == 400

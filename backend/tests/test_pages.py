"""backend/app.py page routes, rendered against an in-memory SQLite provider and the mock LLM.

StrictUndefined turns any template variable the route does not supply into a test failure.
"""

import pytest
from jinja2 import StrictUndefined

import app as flask_app
import db
import seed_data
from json_api.config import Settings
from json_api.dev.fake_provider import InMemoryProjectDataProvider
from json_api.llm.mock import MockLLMProvider
from sqlite_provider import SQLiteProjectDataProvider


def make_pages_client(data_provider, data_mode="injected"):
    app = flask_app.create_app(
        settings=Settings(data_mode=data_mode),
        config={"DATABASE": ":memory:", "TESTING": True},
        data_provider=data_provider,
        llm_provider=MockLLMProvider(),
    )
    app.jinja_env.undefined = StrictUndefined
    return app.test_client()


@pytest.fixture
def client(monkeypatch):
    conn = db.connect_memory()
    # ":memory:" gives every request a fresh empty database; the forum page queries tables, so
    # all requests share this one connection instead.
    monkeypatch.setattr(db, "get_db", lambda: conn)
    yield make_pages_client(SQLiteProjectDataProvider(lambda: conn))
    conn.close()


PROFILE = {
    "username": "sam_builds",
    "major": "Physics",
    "interests": ["optics", "astronomy"],
    "other_interests": "telescopes",
    "timeframe": "month",
    "difficulty": "intermediate",
}


@pytest.mark.parametrize("path", ["/", "/forum"])
def test_static_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")
    assert b"Research Rabbit" in response.data  # base.html navbar


def test_landing_opens_the_profile_modal_for_a_new_visitor(client):
    page = client.get("/").get_data(as_text=True)
    modal_tag = page.split('id="interestModal"')[1].split(">")[0]
    assert "hidden" not in modal_tag  # the pop-up is open for a first visit
    for major in seed_data.MAJORS:
        assert major in page
    assert "Seal Your Profile" in page


def test_dashboard_without_a_profile_redirects_to_the_landing_form(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/?new=1")


def test_profile_form_creates_the_user_and_opens_their_dashboard(client):
    response = client.post("/users", data=PROFILE)
    assert response.status_code == 302 and response.headers["Location"].endswith("/dashboard")

    page = client.get("/dashboard").get_data(as_text=True)
    assert "Welcome, sam_builds" in page
    assert "Physics" in page and "telescopes" in page
    assert "Your profile is sealed" in page
    assert 'id="row-recommended"' in page
    assert "DIY Spectroscope for Lamp and Star Spectra" in page  # optics + astronomy, 25 h

    users = client.get("/api/users").json["users"]
    assert users[-1]["username"] == "sam_builds"


def test_profile_form_rejects_bad_input_and_keeps_what_was_typed(client):
    bad = {**PROFILE, "username": "x"}
    response = client.post("/users", data=bad)
    assert response.status_code == 400
    page = response.get_data(as_text=True)
    assert "Pick a username" in page
    assert 'value="Physics" selected' in page  # the form is refilled
    assert len(client.get("/api/users").json["users"]) == len(seed_data.USERS)


def test_same_username_re_enters_instead_of_duplicating(client):
    client.post("/users", data=PROFILE)
    again = client.post("/users", data={**PROFILE, "major": "Biology"})
    assert again.status_code == 302
    users = client.get("/api/users").json["users"]
    assert [u["username"] for u in users].count("sam_builds") == 1
    assert "Welcome back, sam_builds" in client.get("/dashboard").get_data(as_text=True)


def test_switching_user_changes_the_dashboard(client):
    client.post("/session/1", data={"next": "/dashboard"})
    alex = client.get("/dashboard").get_data(as_text=True)
    client.post("/session/2", data={"next": "/dashboard"})
    maya = client.get("/dashboard").get_data(as_text=True)
    assert "Welcome back, alex_demo" in alex and "Welcome back, maya_demo" in maya
    assert "Smart Soil Moisture Monitor" in alex.split('id="row-major"')[0]
    assert "Language Learning Progress Dashboard" in maya.split('id="row-major"')[0]
    assert client.post("/session/999").status_code == 404


def test_dashboard_has_netflix_rows_for_every_axis(client):
    page = client.get("/dashboard/1").get_data(as_text=True)
    for row in ("recommended", "major", "interest-sensors", "difficulty-beginner", "time-weekend"):
        assert f'id="row-{row}"' in page, row
    assert "fictional fixtures" not in page  # the fake-data banner only shows in fake mode


def test_dashboard_unknown_user_is_404(client):
    assert client.get("/dashboard/999").status_code == 404
    assert client.get("/dashboard/not-a-number").status_code == 404


def test_dashboard_in_fake_mode_shows_the_demo_banner():
    client = make_pages_client(InMemoryProjectDataProvider(), data_mode="fake")
    page = client.get("/dashboard/fixture-cs").get_data(as_text=True)
    assert "Welcome back, maya_demo" in page
    assert "fictional fixtures" in page


def test_project_page_shows_outline_materials_and_resources(client):
    client.post("/session/1")
    response = client.get("/projects/1")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    first = seed_data.PROJECTS[0]
    assert first["name"] in page
    assert first["getting_started"].splitlines()[0] in page
    assert first["materials"][0]["name"] in page
    assert first["resources"][0]["title"] in page
    assert 'id="personalizeBtn"' in page  # a student is signed in
    assert "web search unavailable" in page  # no SERPAPI_API_KEY in tests
    assert client.get("/projects/999").status_code == 404


def test_project_page_without_a_profile_offers_to_create_one(client):
    page = client.get("/projects/1").get_data(as_text=True)
    assert "Create a profile to personalize" in page


def test_api_is_mounted_on_the_same_app(client):
    body = client.get("/api/users").json
    assert body["data_source"] == "sqlite"
    assert [u["id"] for u in body["users"]][:2] == ["1", "2"]


def test_dashboard_reports_a_broken_database_instead_of_an_empty_page():
    conn = db.connect_memory()
    conn.close()
    client = make_pages_client(SQLiteProjectDataProvider(lambda: conn))
    response = client.get("/dashboard/1")
    assert response.status_code == 503
    assert response.json["error"]["code"] == "DATA_UNAVAILABLE"


def test_forum_lists_seeded_posts_and_accepts_a_post(client):
    page = client.get("/forum").get_data(as_text=True)
    assert "Soil sensor readings are noisy" in page
    response = client.post(
        "/forum/posts",
        data={"user_id": "1", "title": "Hello", "body": "First post", "project_id": ""},
    )
    assert response.status_code == 302
    assert "Hello" in client.get("/forum").get_data(as_text=True)

"""backend/app.py page routes, rendered against an in-memory SQLite provider and the mock LLM.

StrictUndefined turns any template variable the route does not supply into a test failure.
"""

import pytest
from jinja2 import StrictUndefined

import app as flask_app
import db
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
def client():
    conn = db.connect_memory()
    yield make_pages_client(SQLiteProjectDataProvider(lambda: conn))
    conn.close()


@pytest.mark.parametrize("path", ["/", "/forum"])
def test_static_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")
    assert b"Research Rabbit" in response.data  # base.html navbar


def test_dashboard_shows_the_users_ranked_projects(client):
    response = client.get("/dashboard/1")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Welcome back, alex_demo" in page
    assert "Smart Soil Moisture Monitor" in page
    assert "fictional fixtures" not in page  # the fake-data banner only shows in fake mode


def test_dashboard_unknown_user_is_404(client):
    assert client.get("/dashboard/999").status_code == 404
    assert client.get("/dashboard/not-a-number").status_code == 404


def test_dashboard_in_fake_mode_shows_the_demo_banner():
    client = make_pages_client(InMemoryProjectDataProvider(), data_mode="fake")
    page = client.get("/dashboard/fixture-cs").get_data(as_text=True)
    assert "Welcome back, maya_demo" in page
    assert "fictional fixtures" in page


def test_api_is_mounted_on_the_same_app(client):
    body = client.get("/api/users").json
    assert body["data_source"] == "sqlite"
    assert [u["id"] for u in body["users"]] == ["1", "2"]


def test_dashboard_reports_a_broken_database_instead_of_an_empty_page():
    conn = db.connect_memory()
    conn.close()
    client = make_pages_client(SQLiteProjectDataProvider(lambda: conn))
    response = client.get("/dashboard/1")
    assert response.status_code == 503
    assert response.json["code"] == "DATA_UNAVAILABLE"

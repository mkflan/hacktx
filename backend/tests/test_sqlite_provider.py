"""SQLite provider against an in-memory database built from schema.sql + seed.sql. No file."""

import sqlite3

import pytest

import db
from json_api.config import Settings
from json_api.dev.fake_provider import InMemoryProjectDataProvider
from json_api.dev.fixtures import FIXTURE_PROJECTS, FIXTURE_USERS
from json_api.llm.mock import MockLLMProvider
from sqlite_provider import SQLiteProjectDataProvider, split_list


def memory_db(seed=True) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    db.apply_schema(conn, seed=seed)
    return conn


@pytest.fixture
def conn():
    connection = memory_db()
    yield connection
    connection.close()


@pytest.fixture
def provider(conn):
    return SQLiteProjectDataProvider(lambda: conn)


def test_split_list_trims_and_drops_empties_and_duplicates():
    assert split_list(" sensors, plants,,IoT ,plants") == ("sensors", "plants", "IoT")
    assert split_list(None) == ()


def test_seeded_users_match_the_fixtures_with_integer_ids(provider):
    users = provider.list_users()
    assert [u.id for u in users] == ["1", "2"]
    for got, want in zip(users, FIXTURE_USERS, strict=True):
        assert got.model_dump(exclude={"id"}) == want.model_dump(exclude={"id"})


def test_seeded_projects_match_the_fixtures(provider):
    projects = provider.list_projects()
    assert [p.id for p in projects] == [str(i) for i in range(1, 11)]
    for got, want in zip(projects, FIXTURE_PROJECTS, strict=True):
        assert got.model_dump(exclude={"id", "resources"}) == want.model_dump(
            exclude={"id", "resources"}
        )
        assert [r.model_dump(exclude={"id"}) for r in got.resources] == [
            r.model_dump(exclude={"id"}) for r in want.resources
        ]
    assert projects[0].resources[0].id == "1/arduino-getting-started"


def test_weeks_only_timeline_gets_no_invented_hours(provider):
    greenhouse = provider.get_project("3")
    assert greenhouse.timeline.unit == "weeks"
    assert greenhouse.timeline.estimated_total_hours is None


def test_unknown_or_non_numeric_ids_are_not_found(provider):
    assert provider.get_user("999") is None
    assert provider.get_user("fixture-ece") is None
    assert provider.get_project("abc") is None
    assert provider.get_project("1").name == "Smart Soil Moisture Monitor"


def test_seed_is_idempotent(conn):
    db.apply_schema(conn)
    assert conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 10
    assert conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0] == 9


def test_old_skeleton_database_is_refused_not_misread():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, major TEXT, interests TEXT);"
    )
    with pytest.raises(RuntimeError, match="Delete backend/app.db"):
        db.apply_schema(conn)


def test_api_routes_serve_sqlite_data(make_client, provider):
    client = make_client(
        data_provider=provider,
        llm_provider=MockLLMProvider(),
        settings_override=Settings(data_mode="injected"),
    )
    users = client.get("/api/users").json
    assert users["data_source"] == "sqlite"
    assert [u["username"] for u in users["users"]] == ["alex_demo", "maya_demo"]

    recs = client.post("/api/users/1/recommendations", json={}).json
    assert recs["data_source"] == "sqlite"
    fake = make_client(data_provider=InMemoryProjectDataProvider(), llm_provider=MockLLMProvider())
    fake_recs = fake.post("/api/users/fixture-ece/recommendations", json={}).json
    names = [c["project"]["name"] for c in recs["projects"]]
    assert names and names == [c["project"]["name"] for c in fake_recs["projects"]]

    assert client.get("/api/users/999").status_code == 404


def test_a_broken_database_is_503_not_an_empty_catalog(make_client):
    conn = memory_db()
    conn.close()
    client = make_client(
        data_provider=SQLiteProjectDataProvider(lambda: conn),
        settings_override=Settings(data_mode="injected"),
    )
    response = client.get("/api/projects")
    assert response.status_code == 503
    assert response.json["error"]["code"] == "DATA_UNAVAILABLE"

"""SQLite provider and the authored catalog, against an in-memory database. No file."""

import sqlite3
from collections import Counter

import pytest

import db
import seed_data
from json_api.config import Settings
from json_api.contracts import NormalizedProject
from json_api.llm.mock import MockLLMProvider
from json_api.services import ranking
from json_api.services.timefit import timeframe_bucket
from sqlite_provider import SQLiteProjectDataProvider, split_list


@pytest.fixture
def conn():
    connection = db.connect_memory()
    yield connection
    connection.close()


@pytest.fixture
def provider(conn):
    return SQLiteProjectDataProvider(lambda: conn)


def test_split_list_trims_and_drops_empties_and_duplicates():
    assert split_list(" sensors, plants,,IoT ,plants") == ("sensors", "plants", "IoT")
    assert split_list(None) == ()


# ---- the authored catalog -------------------------------------------------------------------


def test_catalog_covers_every_major_difficulty_and_timeframe():
    projects = seed_data.PROJECTS
    assert len(projects) >= 45
    majors = Counter(m for p in projects for m in p["majors"])
    assert set(majors) == set(seed_data.MAJORS)
    assert min(majors.values()) >= 5, majors
    assert Counter(p["difficulty"] for p in projects).keys() == set(seed_data.DIFFICULTIES)
    buckets = Counter(
        "weekend" if p["hours"] <= 12 else "two_weeks" if p["hours"] <= 25
        else "month" if p["hours"] <= 45 else "semester"
        for p in projects
    )  # fmt: skip
    assert set(buckets) == {"weekend", "two_weeks", "month", "semester"}


def test_catalog_entries_are_complete_and_distinct():
    slugs = [p["slug"] for p in seed_data.PROJECTS]
    names = [p["name"] for p in seed_data.PROJECTS]
    assert len(set(slugs)) == len(slugs) and len(set(names)) == len(names)
    for p in seed_data.PROJECTS:
        assert p["description"] and p["getting_started"].count("\n") >= 3, p["slug"]
        assert p["interests"] and p["majors"], p["slug"]
        assert any(r["kind"] == "guide" for r in p["resources"]), (p["slug"], "needs a guide")
        for r in p["resources"]:
            if r["url"] is not None:
                assert r["url"].startswith(("https://", "http://")), (p["slug"], r["slug"])
            else:
                assert r["excerpt"], (p["slug"], r["slug"], "text guide needs an excerpt")


# ---- provider mapping -----------------------------------------------------------------------


def test_seeded_users_have_profiles_and_integer_ids(provider):
    users = provider.list_users()
    assert [u.id for u in users][:2] == ["1", "2"]
    assert [u.username for u in users][:2] == ["alex_demo", "maya_demo"]
    alex, maya = users[:2]
    assert alex.skill_level == "beginner" and maya.skill_level == "intermediate"
    assert alex.time_commitment.total_hours == 12 and maya.time_commitment.total_hours == 40
    assert len(users) == len(seed_data.USERS)


def test_seeded_projects_match_the_authored_catalog(provider):
    projects = provider.list_projects()
    assert len(projects) == len(seed_data.PROJECTS)
    for got, want in zip(projects, seed_data.PROJECTS, strict=True):
        assert isinstance(got, NormalizedProject)
        assert got.name == want["name"]
        assert got.associated_majors == tuple(want["majors"])
        assert got.interests == tuple(want["interests"])
        assert got.difficulty == want["difficulty"]
        assert got.timeline.total_hours == want["hours"]
        assert got.getting_started == want["getting_started"]
        assert [m.name for m in got.materials] == [m["name"] for m in want["materials"]]
        assert [r.id.split("/", 1)[1] for r in got.resources] == [
            r["slug"] for r in want["resources"]
        ]
    first = projects[0]
    assert first.resources[0].id == f"{first.id}/{seed_data.PROJECTS[0]['resources'][0]['slug']}"
    assert all(r.source == "authored" for p in projects for r in p.resources)
    assert all(m.shop_url is None for p in projects for m in p.materials)  # not looked up yet


def test_unknown_or_non_numeric_ids_are_not_found(provider):
    assert provider.get_user("999") is None
    assert provider.get_user("fixture-ece") is None
    assert provider.get_project("abc") is None
    assert provider.get_project("1").name == seed_data.PROJECTS[0]["name"]
    assert len(provider.get_project("1").materials) == len(seed_data.PROJECTS[0]["materials"])


def test_seed_is_idempotent(conn):
    before = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
    db.apply_schema(conn)
    assert conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == len(seed_data.PROJECTS)
    assert conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0] == before
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == len(seed_data.USERS)


def test_old_skeleton_database_is_refused_not_misread():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, major TEXT, interests TEXT);"
    )
    with pytest.raises(RuntimeError, match="Delete backend/app.db"):
        db.apply_schema(conn)


# ---- the two demo students see different things -------------------------------------------


def test_demo_users_get_different_recommendations_within_their_limits(provider):
    projects = provider.list_projects()
    alex = provider.get_user("1")
    maya = provider.get_user("2")
    alex_cards, _ = ranking.recommend(alex, projects, None, 12)
    maya_cards, _ = ranking.recommend(maya, projects, None, 12)
    assert alex_cards and maya_cards
    assert {c.project.id for c in alex_cards} != {c.project.id for c in maya_cards}
    # Alex: beginner with 12 hours -> nothing harder or longer than that.
    for card in alex_cards:
        assert card.project.difficulty == "beginner"
        assert card.project.timeline.total_hours <= 12
    # Maya: intermediate with 40 hours -> nothing advanced, nothing over 40 hours.
    for card in maya_cards:
        assert card.project.difficulty in ("beginner", "intermediate")
        assert card.project.timeline.total_hours <= 40
    assert alex_cards[0].project.name == "Smart Soil Moisture Monitor"
    assert any("language learning" in c.project.interests for c in maya_cards)


def test_timeframe_buckets(provider):
    labels = {timeframe_bucket(p.timeline)[1] for p in provider.list_projects()}
    assert labels == {"A weekend", "Two weeks", "A month", "A semester"}


def test_api_routes_serve_sqlite_data(make_client, provider):
    client = make_client(
        data_provider=provider,
        llm_provider=MockLLMProvider(),
        settings_override=Settings(data_mode="injected"),
    )
    users = client.get("/api/users").json
    assert users["data_source"] == "sqlite"
    assert [u["username"] for u in users["users"]][:2] == ["alex_demo", "maya_demo"]

    recs = client.post("/api/users/1/recommendations", json={"limit": 12}).json
    assert recs["data_source"] == "sqlite"
    assert recs["projects"][0]["project"]["name"] == "Smart Soil Moisture Monitor"

    details = client.get("/api/projects/1").json
    assert details["project"]["materials"] and details["project"]["getting_started"]
    assert client.get("/api/users/999").status_code == 404


def test_a_broken_database_is_503_not_an_empty_catalog(make_client):
    conn = db.connect_memory()
    conn.close()
    client = make_client(
        data_provider=SQLiteProjectDataProvider(lambda: conn),
        settings_override=Settings(data_mode="injected"),
    )
    response = client.get("/api/projects")
    assert response.status_code == 503
    assert response.json["error"]["code"] == "DATA_UNAVAILABLE"

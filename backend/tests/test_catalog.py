"""Explore tab: grouping, filters, pagination, facets, details, route order."""

from conftest import ExplodingLLM

from hacktx_app.contracts import NormalizedProject
from hacktx_app.dev.fake_provider import InMemoryProjectDataProvider


def ids_in(body):
    return {p["id"] for g in body["groups"] for p in g["projects"]}


def test_groups_by_major_with_multi_tag_projects_in_several_groups(client):
    body = client.get("/api/projects?group_by=major&limit=100").json
    labels = {g["label"] for g in body["groups"]}
    assert {"Computer Science", "Electrical and Computer Engineering"} <= labels
    groups = {g["key"]: [p["id"] for p in g["projects"]] for g in body["groups"]}
    assert "proj-campus-air" in groups["computer science"]
    assert "proj-campus-air" in groups["electrical and computer engineering"]
    assert body["total"] == 10
    assert body["data_source"] == "fake"


def test_group_by_interest(client):
    body = client.get("/api/projects?group_by=interest&limit=100").json
    keys = {g["key"] for g in body["groups"]}
    assert {"sensors", "language learning", "data visualization"} <= keys


def test_filters_combine_with_and_and_major_aliases(client):
    body = client.get("/api/projects?major=ECE&interest=Plants").json
    assert ids_in(body) == {"proj-soil-moisture", "proj-greenhouse-climate"}
    assert body["total"] == 2


def test_interest_filter_matches_tokens_not_whole_sentences(client):
    body = client.get("/api/projects?interest=sensor").json
    assert "proj-soil-moisture" in ids_in(body)


def test_pagination_is_stable_by_id_and_counts_unique_projects(client):
    first = client.get("/api/projects?limit=3&offset=0").json
    second = client.get("/api/projects?limit=3&offset=3").json
    assert first["total"] == second["total"] == 10
    assert not ids_in(first) & ids_in(second)
    assert ids_in(first) == {"proj-bike-mount", "proj-campus-air", "proj-greenhouse-climate"}


def test_unknown_difficulty_shown_without_filter_and_excluded_with_filter(client):
    unfiltered = client.get("/api/projects?limit=100").json
    assert "proj-greenhouse-climate" in ids_in(unfiltered)
    filtered = client.get("/api/projects?difficulty=beginner&limit=100").json
    assert "proj-greenhouse-climate" not in ids_in(filtered)
    assert "UNKNOWN_DIFFICULTY_EXCLUDED" in {w["code"] for w in filtered["warnings"]}


def test_no_matches_returns_empty_groups_with_warning(client):
    body = client.get("/api/projects?interest=underwater%20basket%20weaving").json
    assert body["groups"] == [] and body["total"] == 0
    assert body["warnings"][0]["code"] == "NO_MATCHES"


def test_bad_query_values_and_unknown_params_are_422(client):
    assert client.get("/api/projects?limit=0").status_code == 422
    assert client.get("/api/projects?limit=101").status_code == 422
    assert client.get("/api/projects?offset=-1").status_code == 422
    assert client.get("/api/projects?difficulty=expert").status_code == 422
    # Explore is shared: it does not take a user.
    assert client.get("/api/projects?user_id=fixture-ece").status_code == 422


def test_facets_come_from_data(client):
    body = client.get("/api/projects/facets").json
    assert {"key": "unknown", "label": "Unknown", "count": 1} in body["difficulties"]
    assert "computer science" in {m["key"] for m in body["majors"]}


def test_static_facets_route_is_not_a_project_id(client):
    assert client.get("/api/projects/facets").status_code == 200
    assert "majors" in client.get("/api/projects/facets").json


def test_project_details_with_missing_optional_fields(client):
    body = client.get("/api/projects/proj-greenhouse-climate").json
    assert body["project"]["difficulty"] is None
    assert body["project"]["timeline"] == {
        "raw": "6 weeks",
        "amount": 6.0,
        "unit": "weeks",
        "estimated_total_hours": None,
    }
    assert set(body["missing_details"]) >= {"difficulty", "resources"}
    assert "NO_RESOURCES" in {w["code"] for w in body["warnings"]}


def test_unknown_project_is_404(client):
    response = client.get("/api/projects/nope")
    assert response.status_code == 404
    assert response.json["error"]["code"] == "PROJECT_NOT_FOUND"


def test_catalog_routes_never_call_llm(make_client, data):
    client = make_client(data_provider=data, llm_provider=ExplodingLLM())
    assert client.get("/api/projects").status_code == 200
    assert client.get("/api/projects/facets").status_code == 200
    assert client.get("/api/projects/proj-vocab-app").status_code == 200


def test_minimal_project_record_is_accepted(make_client):
    data = InMemoryProjectDataProvider(projects=[NormalizedProject(id=1, name="Bare project")])
    body = make_client(data_provider=data).get("/api/projects").json
    assert body["groups"][0]["key"] == "unspecified"
    card = body["groups"][0]["projects"][0]
    assert card["id"] == "1"
    assert "description" in card["missing_fields"]

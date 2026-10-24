"""Prompt tab and catalog personalization with injected fake LLMs."""

from conftest import SpyLLM

from json_api.contracts import NormalizedProject, Resource
from json_api.dev.fake_provider import InMemoryProjectDataProvider
from json_api.dev.fixtures import FIXTURE_PROJECTS
from json_api.llm.mock import MockLLMProvider


def chat(client, user_id, body):
    return client.post(f"/api/users/{user_id}/chat", json=body)


def codes(body):
    return {w["code"] for w in body["warnings"]}


def test_generate_ideas_returns_up_to_limit_concise_cards(client, spy):
    body = chat(client, "fixture-cs", {"mode": "generate_ideas", "topic": "flashcards"}).json
    assert body["mode"] == "generate_ideas" and body["user_id"] == "fixture-cs"
    assert len(body["ideas"]) == 3
    assert set(body["ideas"][0]) == {
        "name", "summary", "suggested_difficulty", "estimated_total_hours",
        "why_it_fits", "skills_to_learn", "assumptions",
    }  # fmt: skip
    assert body["generation_mode"] == "mock" and body["persisted"] is False
    assert body["data_source"] == "fake"
    assert "MOCK_GENERATION" in codes(body)
    one = chat(client, "fixture-cs", {"mode": "generate_ideas", "limit": 1}).json
    assert len(one["ideas"]) == 1


def test_elaborate_idea_returns_full_plan_in_one_call(client, spy):
    idea = "A Spanish flashcard web app that plays audio for each word"
    response = chat(client, "fixture-cs", {"mode": "elaborate_idea", "idea": idea})
    assert response.status_code == 200, response.json
    body = response.json
    assert [name for name, _ in spy.calls] == ["elaborate_idea"]
    assert body["original_idea"] == idea and body["persisted"] is False
    plan = body["project"]
    assert 4 <= len(plan["milestones"]) <= 8
    assert len(plan["customization_ideas"]) == 3
    assert sum(m["estimated_hours"] for m in plan["milestones"]) == plan["estimated_total_hours"]
    assert plan["estimated_total_hours"] <= 20
    assert "id" not in plan  # not a database project


def test_stored_user_reaches_the_provider(client, spy):
    chat(client, "fixture-ece", {"mode": "elaborate_idea", "idea": "plant watering robot"})
    _, args = spy.calls[0]
    assert args["user"].major == "Electrical and Computer Engineering"
    assert args["user"].time_commitment.amount == 12


def test_body_cannot_override_identity_or_profile(client):
    for extra in ({"major": "CS"}, {"user_id": "fixture-cs"}, {"interests": ["x"]}):
        body = {"mode": "elaborate_idea", "idea": "robot", **extra}
        assert chat(client, "fixture-ece", body).status_code == 422


def test_preferences_stay_request_local(client, spy):
    prefs = {"skill_level": "advanced", "budget_usd": 25}
    chat(client, "fixture-ece", {"mode": "elaborate_idea", "idea": "robot", "preferences": prefs})
    chat(client, "fixture-ece", {"mode": "elaborate_idea", "idea": "robot two"})
    assert spy.calls[0][1]["preferences"].skill_level == "advanced"
    assert spy.calls[1][1]["preferences"] is None


def test_chat_validation_errors_are_422(client):
    assert chat(client, "fixture-ece", {"mode": "elaborate_idea", "idea": ""}).status_code == 422
    long_idea = {"mode": "elaborate_idea", "idea": "x" * 2001}
    assert chat(client, "fixture-ece", long_idea).status_code == 422
    assert chat(client, "fixture-ece", {"mode": "small_talk"}).status_code == 422
    assert chat(client, "fixture-ece", {"mode": "generate_ideas", "limit": 4}).status_code == 422
    bad_prefs = {"mode": "generate_ideas", "preferences": {"technical_goals": ["g"] * 11}}
    assert chat(client, "fixture-ece", bad_prefs).status_code == 422
    response = client.post("/api/users/fixture-ece/chat", data="not json")
    assert response.status_code == 422


def test_unknown_user_is_404_before_llm(client, spy):
    response = chat(client, "ghost", {"mode": "elaborate_idea", "idea": "robot"})
    assert response.status_code == 404
    assert spy.calls == []


def test_supplied_references_hydrate_from_records(client):
    response = client.post(
        "/api/users/fixture-ece/projects/proj-soil-moisture/personalize", json={}
    )
    body = response.json
    resource_ids = {r["id"] for r in body["project"]["resources"]}
    assert "proj-soil-moisture/arduino-getting-started" in resource_ids
    arduino = next(r for r in body["project"]["resources"] if r["provider"] == "Arduino")
    assert arduino["url"].startswith("https://docs.arduino.cc/")
    assert arduino["verification_status"] == "provided_unverified"
    assert "RESOURCES_UNVERIFIED" in codes(body)
    assert "NO_RESEARCH_SOURCES" in codes(body)


def test_personalize_preserves_shared_project(client, data):
    before = data.get_project("proj-soil-moisture").model_dump()
    response = client.post(
        "/api/users/fixture-cs/projects/proj-soil-moisture/personalize",
        json={"preferences": {"skill_level": "beginner"}},
    )
    assert response.status_code == 200, response.json
    body = response.json
    assert body["source_project_id"] == "proj-soil-moisture" and body["user_id"] == "fixture-cs"
    assert body["persisted"] is False
    assert data.get_project("proj-soil-moisture").model_dump() == before
    shared = client.get("/api/projects/proj-soil-moisture").json["project"]
    assert shared["name"] == "Smart Soil Moisture Monitor"


def test_personalize_unknown_project_is_404(client):
    response = client.post("/api/users/fixture-cs/projects/nope/personalize", json={})
    assert response.status_code == 404


def test_missing_resources_give_warning_and_labeled_search_suggestions(make_client, spy):
    bare = [p.model_copy(update={"resources": ()}) for p in FIXTURE_PROJECTS]
    client = make_client(data_provider=InMemoryProjectDataProvider(projects=bare), llm_provider=spy)
    body = chat(client, "fixture-ece", {"mode": "elaborate_idea", "idea": "solar charger"}).json
    plan = body["project"]
    assert plan["resources"] == [] and plan["research_connections"] == []
    assert plan["suggested_search_queries"]
    assert "NO_RESOURCES" in codes(body)


class InventingLLM(SpyLLM):
    """Returns a plan that cites a resource that was never supplied."""

    def elaborate_idea(self, user, preferences, idea, resource_bank):
        draft = MockLLMProvider().elaborate_idea(user, preferences, idea, resource_bank)
        return draft.model_copy(update={"research_resource_ids": ["made-up-paper-2024"]})


def test_invented_resource_ids_fail_validation(make_client, data):
    client = make_client(data_provider=data, llm_provider=InventingLLM())
    response = chat(client, "fixture-ece", {"mode": "elaborate_idea", "idea": "robot"})
    assert response.status_code == 502
    error = response.json["error"]
    assert error["code"] == "LLM_INVALID_OUTPUT"
    assert "made-up-paper-2024" in error["details"][0]["msg"]


def test_non_research_item_cannot_be_cited_as_research(make_client, data):
    class MislabelingLLM(SpyLLM):
        def elaborate_idea(self, user, preferences, idea, resource_bank):
            draft = MockLLMProvider().elaborate_idea(user, preferences, idea, resource_bank)
            return draft.model_copy(update={"research_resource_ids": [resource_bank[0].id]})

    client = make_client(data_provider=data, llm_provider=MislabelingLLM())
    response = chat(client, "fixture-ece", {"mode": "elaborate_idea", "idea": "soil sensor"})
    assert response.status_code == 502


def test_real_research_resources_hydrate(make_client, spy):
    note = Resource(
        id="test/research-note", title="Test-only research note", kind="research",
        topic_tags=("sensors",),
    )  # fmt: skip
    project = NormalizedProject(
        id="p1", name="Sensor study", associated_majors=("ECE",), interests=("sensors",),
        resources=(note,),
    )  # fmt: skip
    client = make_client(
        data_provider=InMemoryProjectDataProvider(projects=[project]), llm_provider=spy
    )
    body = chat(client, "fixture-ece", {"mode": "elaborate_idea", "idea": "sensors"}).json
    assert [r["id"] for r in body["project"]["research_connections"]] == ["test/research-note"]
    assert "NO_RESEARCH_SOURCES" not in codes(body)


def test_plan_over_time_budget_is_reported_not_hidden(make_client, data):
    class OverBudgetLLM(SpyLLM):
        def elaborate_idea(self, user, preferences, idea, resource_bank):
            draft = MockLLMProvider().elaborate_idea(user, preferences, idea, resource_bank)
            milestones = [m.model_copy(update={"estimated_hours": 6}) for m in draft.milestones]
            return draft.model_copy(update={"milestones": milestones, "estimated_total_hours": 30})

    client = make_client(data_provider=data, llm_provider=OverBudgetLLM())
    body = chat(client, "fixture-ece", {"mode": "elaborate_idea", "idea": "robot"}).json
    assert body["project"]["estimated_total_hours"] == 30
    assert "PLAN_EXCEEDS_TIME_BUDGET" in codes(body)

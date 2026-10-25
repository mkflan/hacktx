"""Recommendations: signal-supported ranking, time handling, preferences, no LLM."""

from conftest import ExplodingLLM

from json_api.contracts import NormalizedProject, NormalizedUser, TimeValue
from json_api.dev.fake_provider import InMemoryProjectDataProvider
from json_api.dev.fixtures import ALEX, FIXTURE_PROJECTS
from json_api.services.timefit import evaluate_time_fit


def recommend(client, user_id, body=None):
    response = client.post(f"/api/users/{user_id}/recommendations", json=body or {})
    assert response.status_code == 200, response.json
    return response.json


def top_ids(body):
    return [card["project"]["id"] for card in body["projects"]]


def test_fixture_users_get_three_different_signal_supported_matches(client):
    alex = recommend(client, "fixture-ece")
    maya = recommend(client, "fixture-cs")
    assert top_ids(alex) == ["proj-soil-moisture", "proj-solar-logger", "proj-greenhouse-climate"]
    assert top_ids(maya) == ["proj-lang-dashboard", "proj-vocab-app", "proj-phrasebook-chat"]
    assert alex["user_id"] == "fixture-ece" and maya["user_id"] == "fixture-cs"
    for card in alex["projects"] + maya["projects"]:
        assert card["matched_majors"] or card["matched_interests"]


def test_scores_are_explained(client):
    card = recommend(client, "fixture-ece")["projects"][0]
    assert card["score"] == 7.0
    assert card["score_components"] == {
        "major_match": 1.0,
        "interest_overlap": 0.67,
        "time_fit_bonus": 2.0,
        "preference_bonus": 0.0,
    }
    assert card["matched_interests"] == ["sensors", "plants"]
    assert card["time_fit"]["status"] == "fits"
    assert any("12 total hours" in reason for reason in card["reasons"])


def test_known_total_hour_overruns_are_excluded(client):
    body = recommend(client, "fixture-ece")
    assert "proj-water-quality" not in top_ids(body)
    assert "proj-campus-air" not in top_ids(body)
    assert "EXCLUDED_OVER_TIME" in {w["code"] for w in body["warnings"]}


def test_unknown_timeline_gets_warning_not_a_fit_score(client):
    card = recommend(client, "fixture-ece")["projects"][2]
    assert card["project"]["id"] == "proj-greenhouse-climate"
    assert card["score_components"]["time_fit_bonus"] == 0
    assert card["time_fit"]["status"] == "unknown"
    assert "TIME_FIT_UNKNOWN" in {w["code"] for w in card["warnings"]}


def test_weekly_availability_is_not_a_total_cap():
    weekly = TimeValue(amount=5, unit="hours_per_week", raw="5 h/week")
    fit = evaluate_time_fit(weekly, TimeValue(amount=30, unit="total_hours"))
    assert fit.status == "estimated_weeks" and not fit.excluded
    assert fit.estimated_weeks == 6.0 and fit.bonus == 0
    assert "Estimate" in fit.explanation


def test_weeks_are_never_converted_to_hours():
    fit = evaluate_time_fit(
        TimeValue(amount=12, unit="total_hours"), TimeValue(amount=6, unit="weeks")
    )
    assert fit.status == "unknown" and fit.bonus == 0 and not fit.excluded
    fit = evaluate_time_fit(TimeValue(amount=8, unit="weeks"), TimeValue(amount=6, unit="weeks"))
    assert fit.status == "not_comparable" and fit.bonus == 0
    assert TimeValue(amount=6, unit="weeks").total_hours is None


def test_unknown_user_time_is_not_scored():
    fit = evaluate_time_fit(TimeValue(raw="whenever"), TimeValue(amount=5, unit="total_hours"))
    assert fit.status == "unknown" and fit.bonus == 0 and not fit.excluded


def test_weekly_user_keeps_big_projects_with_estimated_weeks(make_client):
    weekly = ALEX.model_copy(
        update={"id": "weekly", "time_commitment": TimeValue(amount=5, unit="hours_per_week")}
    )
    data = InMemoryProjectDataProvider(users=[weekly])
    body = recommend(make_client(data_provider=data), "weekly")
    cards = {c["project"]["id"]: c for c in body["projects"]}
    # 24 total hours would be excluded for a 12-hour cap, but 5 h/week sets no total cap.
    assert cards["proj-campus-air"]["time_fit"]["status"] == "estimated_weeks"
    assert cards["proj-campus-air"]["time_fit"]["estimated_weeks"] == 4.8
    assert "EXCLUDED_OVER_TIME" not in {w["code"] for w in body["warnings"]}


def test_major_aliases_match(make_client):
    alias_user = ALEX.model_copy(update={"id": "alias", "major": " ece "})
    data = InMemoryProjectDataProvider(users=[alias_user])
    body = recommend(make_client(data_provider=data), "alias")
    assert body["projects"][0]["matched_majors"] == ["Electrical and Computer Engineering"]


def test_no_signal_returns_no_recommendations_with_warning(make_client):
    stranger = NormalizedUser(
        id="u1", username="x", major="Art History", interests=("opera",),
        time_commitment=TimeValue(amount=10, unit="total_hours"),
    )  # fmt: skip
    data = InMemoryProjectDataProvider(users=[stranger])
    body = recommend(make_client(data_provider=data), "u1")
    assert body["projects"] == []
    assert "NO_SIGNAL_MATCHES" in {w["code"] for w in body["warnings"]}


def test_rank_changes_when_provider_user_content_changes(client, data):
    before = top_ids(recommend(client, "fixture-ece"))
    data.replace_user(
        ALEX.model_copy(update={"major": "Mechanical Engineering", "interests": ("3d printing",)})
    )
    after = top_ids(recommend(client, "fixture-ece"))
    assert before != after
    assert after[0] == "proj-bike-mount"


def test_skill_preference_excludes_harder_projects_and_keeps_unknown(client):
    body = recommend(client, "fixture-ece", {"preferences": {"skill_level": "beginner"}})
    ids = top_ids(body)
    assert "proj-solar-logger" not in ids  # intermediate > beginner
    assert "proj-greenhouse-climate" in ids  # unknown difficulty stays, with a warning
    unknown = next(c for c in body["projects"] if c["project"]["id"] == "proj-greenhouse-climate")
    assert "UNKNOWN_DIFFICULTY" in {w["code"] for w in unknown["warnings"]}
    beginner = next(c for c in body["projects"] if c["project"]["id"] == "proj-soil-moisture")
    assert beginner["score_components"]["preference_bonus"] == 1.0


def test_goal_keywords_only_boost_when_project_tags_support_them(client):
    body = recommend(client, "fixture-ece", {"preferences": {"technical_goals": ["IoT"]}})
    soil = next(c for c in body["projects"] if c["project"]["id"] == "proj-soil-moisture")
    solar = next(c for c in body["projects"] if c["project"]["id"] == "proj-solar-logger")
    assert soil["score_components"]["preference_bonus"] == 0.5
    assert solar["score_components"]["preference_bonus"] == 0.0


def test_preferences_are_request_local(client):
    recommend(client, "fixture-ece", {"preferences": {"skill_level": "beginner"}})
    body = recommend(client, "fixture-ece")
    assert "proj-solar-logger" in top_ids(body)


def test_body_cannot_override_saved_profile(client):
    response = client.post(
        "/api/users/fixture-ece/recommendations", json={"major": "Computer Science"}
    )
    assert response.status_code == 422
    response = client.post(
        "/api/users/fixture-ece/recommendations",
        json={"preferences": {"interests": ["web apps"]}},
    )
    assert response.status_code == 422


def test_limit_bounds(client):
    assert len(recommend(client, "fixture-ece", {"limit": 1})["projects"]) == 1
    assert (
        client.post("/api/users/fixture-ece/recommendations", json={"limit": 13}).status_code == 422
    )


def test_ties_break_by_project_id(make_client):
    twin = FIXTURE_PROJECTS[0].model_copy(update={"id": "a-twin"})
    data = InMemoryProjectDataProvider(projects=[FIXTURE_PROJECTS[0], twin])
    assert top_ids(recommend(make_client(data_provider=data), "fixture-ece")) == [
        "a-twin",
        "proj-soil-moisture",
    ]


def test_recommendations_never_call_llm(make_client, data):
    client = make_client(data_provider=data, llm_provider=ExplodingLLM())
    assert len(recommend(client, "fixture-cs")["projects"]) == 3


def test_unknown_user_is_404(client):
    response = client.post("/api/users/nobody/recommendations", json={})
    assert response.status_code == 404
    assert response.json["error"] == {
        "code": "USER_NOT_FOUND",
        "message": "No user with id 'nobody'.",
        "retryable": False,
    }


def test_duplicate_project_ids_are_deduplicated(make_client):
    project = NormalizedProject(id="dup", name="One", interests=("sensors",))
    data = InMemoryProjectDataProvider(projects=[project])
    data._projects = None  # replaced by a list with duplicates below
    data.list_projects = lambda: [project, project.model_copy(update={"name": "Two"})]
    body = recommend(make_client(data_provider=data), "fixture-ece")
    assert top_ids(body) == ["dup"]
    assert "DUPLICATE_PROJECT_ID" in {w["code"] for w in body["warnings"]}

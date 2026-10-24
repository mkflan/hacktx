"""A contract-compatible replacement provider works with no route or service changes.

This is a stand-in for the database teammate's future implementation. It is deliberately a
different class with integer IDs and no shared code with the fake provider.
"""

from json_api.contracts import (
    NormalizedProject,
    NormalizedUser,
    ProjectDataProvider,
    Resource,
    TimeValue,
)


class TeammateStyleProvider:
    def __init__(self) -> None:
        self.users = {
            "7": NormalizedUser(
                id=7, username="sam", major="CS", interests=["web apps"],
                time_commitment=TimeValue(amount=4, unit="hours_per_week", raw="4 h/week"),
            )
        }  # fmt: skip
        self.projects = {
            "101": NormalizedProject(
                id=101, name="Club Event Board", associated_majors=["Computer Science"],
                interests=["web apps"], timeline=TimeValue(amount=12, unit="total_hours"),
                resources=[Resource(id="101/r1", title="Club notes", kind="guide",
                                    content_excerpt="Start with a static page.")],
            )
        }  # fmt: skip

    def list_users(self):
        return list(self.users.values())

    def get_user(self, user_id):
        return self.users.get(user_id)

    def list_projects(self):
        return list(self.projects.values())

    def get_project(self, project_id):
        return self.projects.get(project_id)


def test_replacement_satisfies_protocol():
    assert isinstance(TeammateStyleProvider(), ProjectDataProvider)


def test_all_endpoints_work_with_injected_provider(make_client, spy):
    client = make_client(data_provider=TeammateStyleProvider(), llm_provider=spy)
    users = client.get("/api/users").json
    assert users == {"users": [{"id": "7", "username": "sam", "major": "CS"}],
                     "data_source": "injected"}  # fmt: skip
    assert client.get("/api/projects?major=cs").json["total"] == 1
    assert client.get("/api/projects/101").json["project"]["name"] == "Club Event Board"

    recs = client.post("/api/users/7/recommendations", json={}).json
    card = recs["projects"][0]
    assert card["project"]["id"] == "101"
    assert card["time_fit"]["status"] == "estimated_weeks"
    assert card["time_fit"]["estimated_weeks"] == 3.0

    plan = client.post("/api/users/7/chat", json={"mode": "elaborate_idea", "idea": "web app"})
    assert plan.status_code == 200 and plan.json["data_source"] == "injected"
    weekly = [w["hours"] for w in plan.json["project"]["suggested_schedule"]]
    assert max(weekly) <= 4

    personalized = client.post("/api/users/7/projects/101/personalize", json={}).json
    assert personalized["project"]["resources"][0]["id"] == "101/r1"
    assert personalized["project"]["resources"][0]["url"] is None

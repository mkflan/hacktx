"""In-memory ProjectDataProvider for local development and tests. Not a database."""

from collections.abc import Iterable

from ..contracts import NormalizedProject, NormalizedUser
from .fixtures import FIXTURE_PROJECTS, FIXTURE_USERS


class InMemoryProjectDataProvider:
    data_source = "fake"

    def __init__(
        self,
        users: Iterable[NormalizedUser] = FIXTURE_USERS,
        projects: Iterable[NormalizedProject] = FIXTURE_PROJECTS,
    ) -> None:
        self._users = {u.id: u for u in users}
        self._projects = {p.id: p for p in projects}

    def list_users(self) -> list[NormalizedUser]:
        return list(self._users.values())

    def get_user(self, user_id: str) -> NormalizedUser | None:
        return self._users.get(user_id)

    def list_projects(self) -> list[NormalizedProject]:
        return list(self._projects.values())

    def get_project(self, project_id: str) -> NormalizedProject | None:
        return self._projects.get(project_id)

    # Test/dev helper only (not part of the provider contract): simulate a profile edit.
    def replace_user(self, user: NormalizedUser) -> None:
        self._users[user.id] = user

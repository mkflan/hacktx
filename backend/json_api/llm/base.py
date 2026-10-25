"""The injectable LLM provider interface."""

from typing import Protocol, runtime_checkable

from ..api.schemas import PersonalizationPreferences
from ..contracts import NormalizedProject, NormalizedUser, Resource
from .schemas import IdeasDraft, ProjectPlanDraft


@runtime_checkable
class LLMProvider(Protocol):
    """mode is reported as generation_mode ("mock" or "gemini"). model_id goes in cache keys.

    Implementations raise AppError for provider failures (503 unavailable, 502 invalid output).
    """

    mode: str
    model_id: str

    def generate_ideas(
        self,
        user: NormalizedUser,
        preferences: PersonalizationPreferences | None,
        topic: str | None,
        resource_bank: list[Resource],
        limit: int = 3,
    ) -> IdeasDraft: ...

    def elaborate_idea(
        self,
        user: NormalizedUser,
        preferences: PersonalizationPreferences | None,
        idea: str,
        resource_bank: list[Resource],
    ) -> ProjectPlanDraft: ...

    def personalize_project(
        self,
        user: NormalizedUser,
        preferences: PersonalizationPreferences | None,
        project: NormalizedProject,
        resource_bank: list[Resource],
    ) -> ProjectPlanDraft: ...

    def chat(self, system: str, turns: list[tuple[str, str]]) -> str:
        """One conversational reply (plain text / markdown) to the turns, each
        ("user" | "assistant", content). The caller supplies the full system prompt."""
        ...

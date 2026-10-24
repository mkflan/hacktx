"""Shapes the LLM must produce (drafts) and the hydrated plan returned to the browser.

Drafts reference resources only by ID. The service resolves IDs against the in-memory resource
bank built from supplied project records, so the model can never introduce a URL or citation.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from ..contracts import Difficulty, Resource

Line = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=600)]
Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Ids = list[Annotated[str, StringConstraints(min_length=1, max_length=200)]]


class _Draft(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GeneratedIdeaCard(_Draft):
    """A concise new idea. Not a saved project and not yet a full guide."""

    name: Short
    summary: Line
    suggested_difficulty: Difficulty | None
    estimated_total_hours: float = Field(ge=0, le=2000)
    why_it_fits: Line
    skills_to_learn: list[Short] = Field(max_length=10)
    assumptions: list[Line] = Field(max_length=10)


class IdeasDraft(_Draft):
    ideas: list[GeneratedIdeaCard] = Field(min_length=1, max_length=5)


class MaterialItem(_Draft):
    name: Short
    purpose: Line
    quantity: Short | None
    estimated_cost_usd: float | None = Field(ge=0, le=100_000)


class Milestone(_Draft):
    title: Short
    objective: Line
    steps: list[Line] = Field(min_length=1, max_length=12)
    expected_output: Line
    definition_of_done: Line
    pitfalls: list[Line] = Field(max_length=8)
    estimated_hours: float = Field(ge=0, le=500)
    resource_ids: Ids = Field(max_length=10)


class ScheduleEntry(_Draft):
    week: int = Field(ge=1, le=104)
    focus: Line
    hours: float = Field(ge=0, le=168)


class _PlanBody(_Draft):
    name: Short
    summary: Line
    associated_majors: list[Short] = Field(max_length=10)
    interests: list[Short] = Field(max_length=15)
    difficulty: Difficulty | None
    difficulty_assumptions: list[Line] = Field(max_length=10)
    deliverable: Line
    learning_objectives: list[Line] = Field(min_length=1, max_length=12)
    prerequisites: list[Line] = Field(max_length=12)
    estimated_total_hours: float = Field(ge=0, le=2000)
    suggested_schedule: list[ScheduleEntry] = Field(max_length=52)
    estimated_cost_usd: float | None = Field(ge=0, le=100_000)
    materials: list[MaterialItem] = Field(max_length=30)
    software: list[MaterialItem] = Field(max_length=30)
    milestones: list[Milestone] = Field(min_length=4, max_length=8)
    customization_ideas: list[Line] = Field(min_length=3, max_length=3)
    success_criteria: list[Line] = Field(min_length=1, max_length=12)
    first_action: Line
    scope_adjustments: list[Line] = Field(max_length=10)
    constraint_warnings: list[Line] = Field(max_length=10)
    assumptions: list[Line] = Field(max_length=12)
    suggested_search_queries: list[Short] = Field(max_length=8)


class ProjectPlanDraft(_PlanBody):
    """LLM output. Every *_ids field must reference the supplied resource bank."""

    resource_ids: Ids = Field(max_length=20)
    research_resource_ids: Ids = Field(max_length=10)
    example_resource_ids: Ids = Field(max_length=10)


class ProjectPlan(_PlanBody):
    """Returned to the browser. Resource lists come from supplied records, never the model."""

    resources: list[Resource]
    research_connections: list[Resource]
    similar_examples: list[Resource]
    guidance_note: str = (
        "Milestones, steps and estimates are generated guidance, not a sourced third-party "
        "tutorial. Only items in resources/research_connections/similar_examples come from "
        "supplied records."
    )

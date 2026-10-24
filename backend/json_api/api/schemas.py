"""Request and response shapes for the HTTP API. Requests reject unknown fields."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter

from ..contracts import Difficulty, NormalizedProject, TimeValue
from ..services.timefit import TimeFit

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
PathId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class _Request(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PersonalizationPreferences(_Request):
    """Request-only extras. Never saved and never treated as database columns."""

    skill_level: Difficulty | None = None
    technical_goals: list[ShortText] = Field(default_factory=list, max_length=10)
    existing_skills: list[ShortText] = Field(default_factory=list, max_length=20)
    budget_usd: float | None = Field(default=None, ge=0, le=1_000_000)
    available_materials: list[ShortText] = Field(default_factory=list, max_length=20)


class ProjectsQuery(_Request):
    group_by: Literal["major", "interest"] = "major"
    major: ShortText | None = None
    interest: ShortText | None = None
    difficulty: Difficulty | None = None
    limit: int = Field(default=30, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=100_000)


class RecommendationsRequest(_Request):
    limit: int = Field(default=3, ge=1, le=3)
    preferences: PersonalizationPreferences | None = None


class GenerateIdeasRequest(_Request):
    mode: Literal["generate_ideas"]
    topic: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None
    limit: int = Field(default=3, ge=1, le=3)
    preferences: PersonalizationPreferences | None = None


class ElaborateIdeaRequest(_Request):
    mode: Literal["elaborate_idea"]
    idea: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    preferences: PersonalizationPreferences | None = None


ChatRequest = Annotated[GenerateIdeasRequest | ElaborateIdeaRequest, Field(discriminator="mode")]
chat_request_adapter: TypeAdapter[GenerateIdeasRequest | ElaborateIdeaRequest] = TypeAdapter(
    ChatRequest
)


class PersonalizeRequest(_Request):
    preferences: PersonalizationPreferences | None = None


# ---- responses -------------------------------------------------------------------------------


class Notice(BaseModel):
    """A warning or limitation shown to the user. code is stable; message is display text."""

    code: str
    message: str
    project_id: str | None = None


class UserSummary(BaseModel):
    id: str
    username: str
    major: str


class ProjectCard(BaseModel):
    id: str
    name: str
    associated_majors: list[str]
    interests: list[str]
    timeline: TimeValue
    difficulty: Difficulty | None
    description: str | None
    resource_count: int
    missing_fields: list[str]

    @classmethod
    def from_project(cls, project: NormalizedProject) -> ProjectCard:
        return cls(
            id=project.id,
            name=project.name,
            associated_majors=list(project.associated_majors),
            interests=list(project.interests),
            timeline=project.timeline,
            difficulty=project.difficulty,
            description=project.description,
            resource_count=len(project.resources),
            missing_fields=missing_fields(project),
        )


def missing_fields(project: NormalizedProject) -> list[str]:
    missing = []
    if not project.description:
        missing.append("description")
    if project.difficulty is None:
        missing.append("difficulty")
    if not project.timeline.is_known:
        missing.append("timeline")
    elif project.timeline.total_hours is None:
        missing.append("timeline.estimated_total_hours")
    if not project.resources:
        missing.append("resources")
    if not project.associated_majors:
        missing.append("associated_majors")
    if not project.interests:
        missing.append("interests")
    return missing


class ProjectGroup(BaseModel):
    key: str
    label: str
    projects: list[ProjectCard]


class ScoreComponents(BaseModel):
    major_match: float
    interest_overlap: float
    time_fit_bonus: float
    preference_bonus: float


class RecommendationCard(BaseModel):
    project: ProjectCard
    score: float
    score_components: ScoreComponents
    score_note: str = "Heuristic: 3*major_match + 3*interest_overlap + time_fit + preferences."
    matched_majors: list[str]
    matched_interests: list[str]
    time_fit: TimeFit
    reasons: list[str]
    warnings: list[Notice]

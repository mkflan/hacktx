"""Application-facing data contracts.

These DTOs describe what the application needs, not how any database stores it. The database
teammate maps their own records into these shapes inside their ProjectDataProvider
implementation. Every model is frozen: services can never mutate a shared project record.
"""

from typing import Annotated, Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

TimeUnit = Literal["total_hours", "hours_per_week", "weeks", "unknown"]
ResourceKind = Literal["guide", "research", "tutorial", "documentation", "example", "other"]
VerificationStatus = Literal["provided_unverified", "verified"]
Difficulty = Literal["beginner", "intermediate", "advanced"]
DIFFICULTY_ORDER: dict[str, int] = {"beginner": 0, "intermediate": 1, "advanced": 2}


def _to_stable_id(value: Any) -> Any:
    """Accept integer or string IDs at the boundary and normalize them to stripped strings."""
    if isinstance(value, bool):
        raise ValueError("IDs must be strings or integers, not booleans")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return value.strip()
    return value


StableId = Annotated[str, BeforeValidator(_to_stable_id), Field(min_length=1, max_length=200)]
Tag = Annotated[str, Field(min_length=1, max_length=200)]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class TimeValue(_Frozen):
    """A time quantity with an explicit unit.

    total_hours, hours_per_week and weeks are different dimensions and are never converted into
    each other without a stated workload. estimated_total_hours is only filled in when the
    source says so, or when the unit is already total_hours.
    """

    raw: str | None = Field(default=None, max_length=200)
    amount: float | None = Field(default=None, ge=0)
    unit: TimeUnit = "unknown"
    estimated_total_hours: float | None = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def _total_hours_are_their_own_estimate(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("unit") == "total_hours":
            if data.get("estimated_total_hours") is None and data.get("amount") is not None:
                data = {**data, "estimated_total_hours": data["amount"]}
        return data

    @property
    def total_hours(self) -> float | None:
        return self.estimated_total_hours

    @property
    def is_known(self) -> bool:
        return self.unit != "unknown" and self.amount is not None


class Resource(_Frozen):
    """A guide, tutorial, paper or other reference supplied by the data provider.

    url may be None for a text guide stored as content_excerpt. A supplied URL stays
    provided_unverified unless the provider has real evidence it was checked.
    """

    id: StableId
    title: str = Field(min_length=1, max_length=300)
    url: str | None = Field(default=None, max_length=2000)
    kind: ResourceKind = "other"
    provider: str | None = Field(default=None, max_length=200)
    topic_tags: tuple[Tag, ...] = ()
    verification_status: VerificationStatus = "provided_unverified"
    content_excerpt: str | None = Field(default=None, max_length=4000)
    metadata: dict[str, str] = Field(default_factory=dict)


class NormalizedUser(_Frozen):
    id: StableId
    username: str = Field(min_length=1, max_length=100)
    major: str = Field(default="", max_length=200)
    interests: tuple[Tag, ...] = ()
    time_commitment: TimeValue = TimeValue()


class NormalizedProject(_Frozen):
    id: StableId
    name: str = Field(min_length=1, max_length=300)
    associated_majors: tuple[Tag, ...] = ()
    interests: tuple[Tag, ...] = ()
    timeline: TimeValue = TimeValue()
    resources: tuple[Resource, ...] = ()
    description: str | None = Field(default=None, max_length=4000)
    difficulty: Difficulty | None = None


@runtime_checkable
class ProjectDataProvider(Protocol):
    """Read-only data access the application needs. The database teammate implements this.

    Return None (not an exception) for an unknown ID. Raise for real access failures; the app
    turns those into 503 DATA_UNAVAILABLE instead of an empty success.
    """

    def list_users(self) -> list[NormalizedUser]: ...

    def get_user(self, user_id: str) -> NormalizedUser | None: ...

    def list_projects(self) -> list[NormalizedProject]: ...

    def get_project(self, project_id: str) -> NormalizedProject | None: ...

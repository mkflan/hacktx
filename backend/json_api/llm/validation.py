"""Checks applied to every LLM draft, by the real provider (to request one correction) and again
by the services before anything is returned."""

from typing import Any

from pydantic import BaseModel, ValidationError

from ..api.schemas import Notice, PersonalizationPreferences
from ..contracts import NormalizedUser, Resource
from .schemas import IdeasDraft, ProjectPlanDraft

EXAMPLE_KINDS = frozenset({"example", "tutorial", "guide"})


def parse_draft[M: BaseModel](model: type[M], data: Any) -> tuple[M | None, list[str]]:
    try:
        return model.model_validate(data), []
    except ValidationError as exc:
        errors = [
            f"{'.'.join(str(p) for p in e['loc']) or '(root)'}: {e['msg']}"
            for e in exc.errors(include_url=False, include_input=False)
        ]
        return None, errors[:20]


def validate_ideas(draft: IdeasDraft) -> list[str]:
    names = [idea.name.casefold() for idea in draft.ideas]
    if len(set(names)) != len(names):
        return ["ideas: each idea needs a distinct name"]
    return []


def validate_plan(draft: ProjectPlanDraft, bank: list[Resource], user: NormalizedUser) -> list[str]:
    by_id = {r.id: r for r in bank}
    errors: list[str] = []

    def check_ids(field: str, ids: list[str], kinds: frozenset[str] | None = None) -> None:
        for resource_id in ids:
            resource = by_id.get(resource_id)
            if resource is None:
                errors.append(
                    f"{field}: unknown resource id {resource_id!r}; use only ids from resource_bank"
                )
            elif kinds is not None and resource.kind not in kinds:
                errors.append(
                    f"{field}: {resource_id!r} is a {resource.kind}, not one of {sorted(kinds)}"
                )

    check_ids("resource_ids", draft.resource_ids)
    check_ids("research_resource_ids", draft.research_resource_ids, frozenset({"research"}))
    check_ids("example_resource_ids", draft.example_resource_ids, EXAMPLE_KINDS)
    for index, milestone in enumerate(draft.milestones):
        check_ids(f"milestones.{index}.resource_ids", milestone.resource_ids)

    milestone_hours = sum(m.estimated_hours for m in draft.milestones)
    total = draft.estimated_total_hours
    if abs(milestone_hours - total) > max(2.0, 0.2 * total):
        errors.append(
            f"estimated_total_hours ({total:g}) must roughly equal the sum of milestone "
            f"estimated_hours ({milestone_hours:g})"
        )

    time = user.time_commitment
    if time.unit == "hours_per_week" and time.amount is not None:
        for entry in draft.suggested_schedule:
            if entry.hours > time.amount * 1.1 + 0.5:
                errors.append(
                    f"suggested_schedule week {entry.week}: {entry.hours:g} hours exceeds the "
                    f"student's {time.amount:g} hours/week"
                )

    item_costs = sum(item.estimated_cost_usd or 0.0 for item in (*draft.materials, *draft.software))
    if draft.estimated_cost_usd is not None and item_costs > draft.estimated_cost_usd * 1.25 + 5:
        errors.append(
            f"estimated_cost_usd ({draft.estimated_cost_usd:g}) is below the sum of item costs "
            f"({item_costs:g})"
        )
    return errors


def plan_constraint_notices(
    draft: ProjectPlanDraft, user: NormalizedUser, prefs: PersonalizationPreferences | None
) -> list[Notice]:
    """Feasibility problems are reported, never hidden by rewriting the model's estimates."""
    notices: list[Notice] = []
    time = user.time_commitment
    if time.unit == "total_hours" and time.amount is not None:
        if draft.estimated_total_hours > time.amount:
            notices.append(
                Notice(
                    code="PLAN_EXCEEDS_TIME_BUDGET",
                    message=f"Plan estimate ({draft.estimated_total_hours:g} h) is above your "
                    f"{time.amount:g} total hours. See scope_adjustments.",
                )
            )
    if prefs and prefs.budget_usd is not None and draft.estimated_cost_usd is not None:
        if draft.estimated_cost_usd > prefs.budget_usd:
            notices.append(
                Notice(
                    code="PLAN_EXCEEDS_BUDGET",
                    message=f"Estimated cost (${draft.estimated_cost_usd:g}) is above your "
                    f"${prefs.budget_usd:g} budget.",
                )
            )
    return notices

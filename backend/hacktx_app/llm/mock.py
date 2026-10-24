"""Deterministic offline provider for demos and tests. Responses are labeled generation_mode=mock.

Output depends on the selected user and the idea/project text, so switching users visibly
changes results. It only references resource IDs from the supplied bank.
"""

import math

from ..api.schemas import PersonalizationPreferences
from ..contracts import NormalizedProject, NormalizedUser, Resource
from ..services.resources import default_search_queries
from .schemas import (
    GeneratedIdeaCard,
    IdeasDraft,
    MaterialItem,
    Milestone,
    ProjectPlanDraft,
    ScheduleEntry,
)
from .validation import EXAMPLE_KINDS

DEFAULT_HOURS = 12.0
ASSUMED_HOURS_PER_WEEK = 6.0
MILESTONE_SHARES = (0.15, 0.25, 0.3, 0.2, 0.1)
MILESTONE_TITLES = (
    "Set up and scope",
    "Build the core",
    "Make it work end to end",
    "Test and measure",
    "Polish and present",
)


def _title(text: str, words: int = 7) -> str:
    cleaned = " ".join(text.replace("\n", " ").split()[:words]).strip(" .,:;!?")
    return (cleaned[:1].upper() + cleaned[1:])[:120] or "Student Project"


def _skill_assumptions(prefs: PersonalizationPreferences | None) -> list[str]:
    if prefs and prefs.skill_level:
        return [f"Scoped for a {prefs.skill_level} (stated in this request)."]
    return ["Skill level was not given; scoped as a first project in this area (assumption)."]


def _target_hours(user: NormalizedUser, base: float) -> tuple[float, list[str]]:
    time = user.time_commitment
    if time.unit == "total_hours" and time.amount is not None:
        return min(base, time.amount), []
    if time.unit == "hours_per_week" and time.amount is not None:
        return base, []
    return base, [f"Time commitment unknown; planned for about {base:g} total hours."]


class MockLLMProvider:
    mode = "mock"
    model_id = "mock-v1"

    def generate_ideas(
        self,
        user: NormalizedUser,
        preferences: PersonalizationPreferences | None,
        topic: str | None,
        resource_bank: list[Resource],
        limit: int = 3,
    ) -> IdeasDraft:
        interests = list(user.interests) or ["your interests"]
        focus = topic or interests[0]
        hours, time_assumptions = _target_hours(user, DEFAULT_HOURS)
        level = preferences.skill_level if preferences else None
        templates = [
            ("{focus} starter prototype", "Build a small working prototype about {focus}."),
            ("{focus} meets {other}", "Combine {focus} with {other} in one demo-ready tool."),
            ("{focus} data tracker", "Collect and visualize simple data about {focus}."),
        ]
        ideas = []
        for index, (name, summary) in enumerate(templates[:limit]):
            other = interests[(index + 1) % len(interests)]
            ideas.append(
                GeneratedIdeaCard(
                    name=_title(name.format(focus=focus, other=other)),
                    summary=summary.format(focus=focus, other=other),
                    suggested_difficulty=level,
                    estimated_total_hours=hours,
                    why_it_fits=(
                        f"Uses your {user.major or 'major'} background and your interest in "
                        f"{', '.join(interests[:2])}."
                    ),
                    skills_to_learn=[f"{focus} basics", "scoping a small build"],
                    assumptions=_skill_assumptions(preferences) + time_assumptions,
                )
            )
        return IdeasDraft(ideas=ideas)

    def elaborate_idea(
        self,
        user: NormalizedUser,
        preferences: PersonalizationPreferences | None,
        idea: str,
        resource_bank: list[Resource],
    ) -> ProjectPlanDraft:
        return self._plan(
            user,
            preferences,
            name=_title(idea),
            summary=f"A scoped build plan for: {' '.join(idea.split())[:400]}",
            majors=[user.major] if user.major else [],
            interests=list(user.interests),
            base_hours=DEFAULT_HOURS,
            bank=resource_bank,
            focus=idea,
        )

    def personalize_project(
        self,
        user: NormalizedUser,
        preferences: PersonalizationPreferences | None,
        project: NormalizedProject,
        resource_bank: list[Resource],
    ) -> ProjectPlanDraft:
        return self._plan(
            user,
            preferences,
            name=_title(f"{project.name} for {user.username}", words=12),
            summary=project.description or f"A tailored plan for {project.name}.",
            majors=list(project.associated_majors),
            interests=list(project.interests),
            base_hours=project.timeline.total_hours or DEFAULT_HOURS,
            bank=resource_bank,
            focus=project.name,
        )

    def _plan(
        self,
        user: NormalizedUser,
        prefs: PersonalizationPreferences | None,
        *,
        name: str,
        summary: str,
        majors: list[str],
        interests: list[str],
        base_hours: float,
        bank: list[Resource],
        focus: str,
    ) -> ProjectPlanDraft:
        total, assumptions = _target_hours(user, base_hours)
        assumptions = _skill_assumptions(prefs) + assumptions
        scope_adjustments = []
        if total < base_hours:
            scope_adjustments.append(
                f"Trimmed from about {base_hours:g} h to {total:g} h to fit your time budget; "
                "the stretch features moved to customization ideas."
            )

        hours = [round(total * share, 1) for share in MILESTONE_SHARES]
        hours[-1] = round(total - sum(hours[:-1]), 1)
        bank_ids = [r.id for r in bank]
        milestones = [
            Milestone(
                title=title,
                objective=f"{title} for {_title(focus, 6)}.",
                steps=[f"Write down what '{title.lower()}' means for this project.", "Do it."],
                expected_output=f"A working result for the '{title.lower()}' stage.",
                definition_of_done="You can demo this stage to a teammate in under 2 minutes.",
                pitfalls=["Scope creep: park new ideas in a list instead of building them."],
                estimated_hours=hours[index],
                resource_ids=[bank_ids[index % len(bank_ids)]] if bank_ids else [],
            )
            for index, title in enumerate(MILESTONE_TITLES)
        ]

        time = user.time_commitment
        per_week = (
            time.amount if time.unit == "hours_per_week" and time.amount else ASSUMED_HOURS_PER_WEEK
        )
        if not (time.unit == "hours_per_week" and time.amount):
            assumptions.append(f"Schedule assumes about {per_week:g} hours per week.")
        weeks = max(1, math.ceil(total / per_week))
        schedule, remaining = [], total
        for week in range(1, weeks + 1):
            week_hours = round(min(per_week, remaining), 1)
            remaining = round(remaining - week_hours, 1)
            schedule.append(
                ScheduleEntry(week=week, focus=MILESTONE_TITLES[min(week - 1, 4)], hours=week_hours)
            )

        return ProjectPlanDraft(
            name=name,
            summary=summary,
            associated_majors=majors[:10],
            interests=interests[:15],
            difficulty=prefs.skill_level if prefs else None,
            difficulty_assumptions=[] if prefs and prefs.skill_level else assumptions[:1],
            deliverable=f"A working demo of '{_title(focus, 8)}' plus a one-page write-up.",
            learning_objectives=[f"Apply {i} in a working build" for i in interests[:3]]
            or ["Plan and ship a small project"],
            prerequisites=["Install the tools listed under software before milestone 1."],
            estimated_total_hours=total,
            suggested_schedule=schedule,
            estimated_cost_usd=None,
            materials=[],
            software=[
                MaterialItem(
                    name="Code editor (VS Code)",
                    purpose="Write and run code",
                    quantity=None,
                    estimated_cost_usd=0.0,
                )
            ],
            milestones=milestones,
            customization_ideas=[
                f"Add a feature tied to {interests[0] if interests else 'your interests'}.",
                "Add a simple data log and chart of results.",
                "Write a short how-to so another student can rebuild it.",
            ],
            success_criteria=[
                "Every milestone's definition of done is met.",
                "A 2-minute demo works.",
            ],
            first_action="Spend 20 minutes writing the one-sentence goal and the demo to show.",
            scope_adjustments=scope_adjustments,
            constraint_warnings=[],
            assumptions=assumptions + ["Cost was not estimated in mock mode."],
            suggested_search_queries=[] if bank else default_search_queries(focus, interests),
            resource_ids=bank_ids[:5],
            research_resource_ids=[r.id for r in bank if r.kind == "research"][:3],
            example_resource_ids=[r.id for r in bank if r.kind in EXAMPLE_KINDS][:3],
        )

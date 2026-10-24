"""Recommendations tab: deterministic, explainable ranking. Never calls the LLM.

score = 3*major_match + 3*interest_overlap + time_fit_bonus + preference_bonus
  major_match       1 if the project lists the user's major (aliases handled), else 0
  interest_overlap  fraction of the user's interests matched by the project's tags (0..1)
  time_fit_bonus    2 when known total hours fit a known total-hours cap, else 0
  preference_bonus  +1 for an exact skill/difficulty match, +0.5 per technical goal keyword
                    found in the project's tags (capped at 1); only with request preferences
"""

from ..api.schemas import (
    Notice,
    PersonalizationPreferences,
    ProjectCard,
    RecommendationCard,
    ScoreComponents,
)
from ..contracts import DIFFICULTY_ORDER, NormalizedProject, NormalizedUser
from .catalog import unique_projects
from .normalize import majors_match, matched_interests, tags_match, unique_tags
from .timefit import evaluate_time_fit

MAJOR_WEIGHT = 3.0
INTEREST_WEIGHT = 3.0
SKILL_MATCH_BONUS = 1.0
GOAL_BONUS_EACH = 0.5
GOAL_BONUS_CAP = 1.0


def _score_project(
    user: NormalizedUser, project: NormalizedProject, prefs: PersonalizationPreferences | None
) -> tuple[RecommendationCard | None, str | None]:
    """Return (card, exclusion_reason). card is None when the project is excluded."""
    time_fit = evaluate_time_fit(user.time_commitment, project.timeline)
    if time_fit.excluded:
        return None, "time"

    notices: list[Notice] = []
    reasons: list[str] = []
    preference_bonus = 0.0

    if prefs and prefs.skill_level:
        if project.difficulty is None:
            notices.append(
                Notice(
                    code="UNKNOWN_DIFFICULTY",
                    message="Project difficulty is unknown, so your skill level was not compared.",
                    project_id=project.id,
                )
            )
        elif DIFFICULTY_ORDER[project.difficulty] > DIFFICULTY_ORDER[prefs.skill_level]:
            return None, "difficulty"
        elif project.difficulty == prefs.skill_level:
            preference_bonus += SKILL_MATCH_BONUS
            reasons.append(f"Difficulty ({project.difficulty}) matches your stated skill level.")
        else:
            reasons.append(
                f"Difficulty ({project.difficulty}) is below your stated skill level; "
                "consider the stretch ideas."
            )

    if prefs and prefs.technical_goals:
        goal_hits = [
            g for g in prefs.technical_goals if any(tags_match(g, t) for t in project.interests)
        ]
        if goal_hits:
            preference_bonus += min(GOAL_BONUS_CAP, GOAL_BONUS_EACH * len(goal_hits))
            reasons.append(
                "Goal keyword(s) appear in the project tags (not a verified skill match): "
                + ", ".join(goal_hits)
            )

    majors = majors_match(user.major, project.associated_majors)
    user_interests = unique_tags(user.interests)
    interests = matched_interests(user_interests, project.interests)
    overlap = len(interests) / len(user_interests) if user_interests else 0.0

    if not majors and not interests:
        return None, "no_signal"

    if majors:
        reasons.insert(0, f"Matches your major ({user.major}).")
    if interests:
        reasons.insert(1 if majors else 0, "Shares your interests: " + ", ".join(interests) + ".")
    reasons.append(time_fit.explanation)
    if time_fit.warning:
        notices.append(
            Notice(code="TIME_FIT_UNKNOWN", message=time_fit.warning, project_id=project.id)
        )
    if project.difficulty is None and not (prefs and prefs.skill_level):
        notices.append(
            Notice(
                code="UNKNOWN_DIFFICULTY",
                message="Project difficulty is not recorded.",
                project_id=project.id,
            )
        )

    components = ScoreComponents(
        major_match=1.0 if majors else 0.0,
        interest_overlap=round(overlap, 2),
        time_fit_bonus=time_fit.bonus,
        preference_bonus=round(preference_bonus, 2),
    )
    score = (
        MAJOR_WEIGHT * components.major_match
        + INTEREST_WEIGHT * overlap
        + components.time_fit_bonus
        + components.preference_bonus
    )
    card = RecommendationCard(
        project=ProjectCard.from_project(project),
        score=round(score, 2),
        score_components=components,
        matched_majors=majors,
        matched_interests=interests,
        time_fit=time_fit,
        reasons=reasons,
        warnings=notices,
    )
    return card, None


def recommend(
    user: NormalizedUser,
    projects: list[NormalizedProject],
    prefs: PersonalizationPreferences | None,
    limit: int,
) -> tuple[list[RecommendationCard], list[Notice]]:
    ordered, notices = unique_projects(projects)
    cards: list[RecommendationCard] = []
    excluded = {"time": 0, "difficulty": 0, "no_signal": 0}
    for project in ordered:
        card, reason = _score_project(user, project, prefs)
        if card is None:
            excluded[reason] += 1
        else:
            cards.append(card)

    # Highest score first; ties broken by normalized project ID.
    cards.sort(key=lambda c: (-c.score, project_sort_key_from_card(c)))
    top = cards[:limit]

    if excluded["time"]:
        notices.append(
            Notice(
                code="EXCLUDED_OVER_TIME",
                message=f"{excluded['time']} project(s) were left out: estimated total hours "
                "exceed your total-hours budget.",
            )
        )
    if excluded["difficulty"]:
        notices.append(
            Notice(
                code="EXCLUDED_DIFFICULTY",
                message=f"{excluded['difficulty']} project(s) were left out: harder than your "
                "stated skill level.",
            )
        )
    if not top:
        notices.append(
            Notice(
                code="NO_SIGNAL_MATCHES",
                message="No project matches your major or interests yet. Try the Explore tab or "
                "generate new ideas in the Prompt tab.",
            )
        )
    elif len(top) < limit:
        notices.append(
            Notice(
                code="FEWER_THAN_LIMIT",
                message=f"Only {len(top)} project(s) had a real match signal.",
            )
        )
    if not prefs or prefs.skill_level is None:
        notices.append(
            Notice(
                code="SKILL_LEVEL_UNKNOWN",
                message="No skill level was given, so difficulty did not affect ranking.",
            )
        )
    return top, notices


def project_sort_key_from_card(card: RecommendationCard) -> tuple[str, str]:
    return (card.project.id.casefold(), card.project.id)

"""Compare a user's time commitment with a project's timeline without mixing dimensions."""

from typing import Literal

from pydantic import BaseModel

from ..contracts import TimeValue

TimeFitStatus = Literal["fits", "exceeds", "estimated_weeks", "not_comparable", "unknown"]
TIME_FIT_BONUS = 2.0


class TimeFit(BaseModel):
    status: TimeFitStatus
    bonus: float = 0.0
    excluded: bool = False
    explanation: str
    estimated_weeks: float | None = None
    warning: str | None = None


def _fmt(value: float) -> str:
    return f"{value:g}"


# Dashboard rows and the landing form share these buckets of estimated total hours.
TIMEFRAME_BUCKETS: tuple[tuple[str, str, float | None], ...] = (
    ("weekend", "A weekend", 12),
    ("two_weeks", "Two weeks", 25),
    ("month", "A month", 45),
    ("semester", "A semester", None),
)


def timeframe_bucket(value: TimeValue) -> tuple[str, str] | None:
    """(key, label) for a timeline with known total hours; None when hours are unknown."""
    hours = value.total_hours
    if hours is None:
        return None
    for key, label, cap in TIMEFRAME_BUCKETS:
        if cap is None or hours <= cap:
            return key, label
    return None


def timeframe_label(value: TimeValue) -> str:
    bucket = timeframe_bucket(value)
    return bucket[1] if bucket else "Timeframe unknown"


def describe(value: TimeValue) -> str:
    if value.raw:
        return value.raw
    if value.amount is None or value.unit == "unknown":
        return "unknown"
    return f"{_fmt(value.amount)} {value.unit.replace('_', ' ')}"


def evaluate_time_fit(user_time: TimeValue, project_time: TimeValue) -> TimeFit:
    project_total = project_time.total_hours

    if not user_time.is_known:
        return TimeFit(
            status="unknown",
            explanation="Your time commitment is unknown, so time fit was not scored.",
            warning="User time commitment is unknown; time fit not scored.",
        )

    if user_time.unit == "total_hours":
        cap = user_time.amount
        if project_total is None:
            return TimeFit(
                status="unknown",
                explanation=(
                    f"Project timeline ({describe(project_time)}) has no total-hours estimate, "
                    f"so it cannot be compared with your {_fmt(cap)} total hours."
                ),
                warning="Project timeline has no total-hours estimate; time fit not scored.",
            )
        if project_total <= cap:
            return TimeFit(
                status="fits",
                bonus=TIME_FIT_BONUS,
                explanation=(
                    f"Estimated {_fmt(project_total)} total hours fits your "
                    f"{_fmt(cap)} total hours."
                ),
            )
        return TimeFit(
            status="exceeds",
            excluded=True,
            explanation=(
                f"Estimated {_fmt(project_total)} total hours exceeds your {_fmt(cap)} total hours."
            ),
        )

    if user_time.unit == "hours_per_week":
        per_week = user_time.amount
        if project_total is not None and per_week > 0:
            weeks = round(project_total / per_week, 1)
            return TimeFit(
                status="estimated_weeks",
                estimated_weeks=weeks,
                explanation=(
                    f"Estimate: about {_fmt(weeks)} weeks at your {_fmt(per_week)} hours/week "
                    f"({_fmt(project_total)} total hours). Weekly availability sets no total cap."
                ),
            )
        return TimeFit(
            status="unknown",
            explanation=(
                f"Project timeline ({describe(project_time)}) has no total-hours estimate, so "
                f"weeks at {_fmt(per_week)} hours/week cannot be estimated."
            ),
            warning="Project timeline has no total-hours estimate; time fit not scored.",
        )

    # user_time.unit == "weeks": a calendar span, not a workload.
    if project_time.unit == "weeks" and project_time.amount is not None:
        verb = "fits within" if project_time.amount <= user_time.amount else "is longer than"
        return TimeFit(
            status="not_comparable",
            explanation=(
                f"Project spans {_fmt(project_time.amount)} weeks, which {verb} your "
                f"{_fmt(user_time.amount)} weeks. Calendar span only, no workload score."
            ),
        )
    return TimeFit(
        status="not_comparable",
        explanation=(
            f"Your availability is a calendar span ({_fmt(user_time.amount)} weeks) and the "
            f"project timeline is {describe(project_time)}; no workload comparison is made."
        ),
        warning="Time commitment and project timeline use different units; not scored.",
    )

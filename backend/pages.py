"""HTML pages: landing, profile form, dashboard, project page, chat page and the forum.

Pages call json_api.services directly (no HTTP hop) and read SQLite through the injected
provider. The current student is a signed cookie set by the landing form; there is no login.
"""

from flask import (
    Blueprint,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import db
import forum
import profiles
from json_api.api.schemas import ProjectCard
from json_api.contracts import NormalizedProject, NormalizedUser
from json_api.dependencies import get_context
from json_api.errors import AppError
from json_api.services import ranking
from json_api.services.normalize import majors_match, tags_match
from json_api.services.timefit import TIMEFRAME_BUCKETS, timeframe_bucket
from seed_data import DIFFICULTIES, FEATURED_INTERESTS, MAJORS, TIMEFRAME_OPTIONS

pages = Blueprint("pages", __name__)

RECOMMENDED_LIMIT = 12
ROW_LIMIT = 12


# ---- current user ---------------------------------------------------------------------------


def current_user() -> NormalizedUser | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    try:
        return get_context().data.get_user(str(user_id))
    except AppError:
        return None


@pages.app_context_processor
def inject_nav():
    ctx = get_context()
    try:
        users = ctx.data.list_users() if ctx.data_provider is not None else []
    except AppError:
        users = []
    return {"current_user": current_user(), "demo_users": users[:10]}


@pages.app_template_filter("timeframe")
def timeframe_filter(timeline) -> str:
    bucket = timeframe_bucket(timeline) if timeline is not None else None
    return bucket[1] if bucket else "Timeframe unknown"


@pages.app_template_filter("hours")
def hours_filter(value) -> str:
    return f"{value:g}" if isinstance(value, int | float) else "?"


# ---- landing and profile ---------------------------------------------------------------------


def _render_landing(error=None, status=200, form=None, open_modal=False):
    return render_template(
        "index.html",
        majors=MAJORS,
        featured_interests=FEATURED_INTERESTS,
        timeframes=TIMEFRAME_OPTIONS,
        difficulties=DIFFICULTIES,
        error=error,
        form=form or {},
        open_modal=open_modal or error is not None,
    ), status


@pages.route("/")
def index():
    return _render_landing(open_modal=current_user() is None or "new" in request.args)


@pages.route("/users", methods=["POST"])
def create_profile():
    try:
        user_id, created = profiles.create_or_enter(db.get_db(), request.form)
    except profiles.ProfileError as exc:
        return _render_landing(error=exc.message, status=exc.status, form=request.form)
    session["user_id"] = str(user_id)
    session["welcome"] = "new" if created else "back"
    return redirect(url_for("pages.dashboard"))


@pages.route("/session/<user_id>", methods=["POST"])
def switch_user(user_id: str):
    """Demo switcher in the nav: become one of the existing students."""
    if get_context().data.get_user(user_id) is None:
        abort(404)
    session["user_id"] = user_id
    session.pop("welcome", None)
    return redirect(request.form.get("next") or url_for("pages.dashboard"))


# ---- dashboard ------------------------------------------------------------------------------


def _card(project: NormalizedProject) -> dict:
    card = ProjectCard.from_project(project).model_dump(mode="json")
    bucket = timeframe_bucket(project.timeline)
    card["timeframe"] = bucket[1] if bucket else "Timeframe unknown"
    card["hours"] = project.timeline.total_hours
    return card


def _row(key: str, title: str, subtitle: str, projects, limit: int = ROW_LIMIT) -> dict | None:
    cards = [_card(p) for p in projects[:limit]]
    return {"key": key, "title": title, "subtitle": subtitle, "cards": cards} if cards else None


def build_rows(user: NormalizedUser, projects: list[NormalizedProject]) -> tuple[list, list]:
    """Netflix-style rows: recommended first, then the student's own major and interests, then
    every difficulty, timeframe and the other majors."""
    cards, notices = ranking.recommend(user, projects, None, RECOMMENDED_LIMIT)
    rows = []
    recommended = {
        "key": "recommended",
        "title": f"Recommended for {user.username}",
        "subtitle": "Ranked on your major, interests, time and difficulty.",
        "cards": [{**_card_from_rec(c), "reasons": c.reasons} for c in cards],
    }
    rows.append(recommended)

    if user.major:
        own = [p for p in projects if majors_match(user.major, p.associated_majors)]
        rows.append(
            _row("major", f"More for {user.major}", "Every project tagged with your major.", own)
        )
    for interest in user.interests:
        liked = [p for p in projects if any(tags_match(interest, t) for t in p.interests)]
        rows.append(_row(f"interest-{interest}", f"Because you like {interest}", "", liked))
    for level in DIFFICULTIES:
        rows.append(
            _row(
                f"difficulty-{level}",
                f"{level.capitalize()} projects",
                "",
                [p for p in projects if p.difficulty == level],
            )
        )
    for key, label, _cap in TIMEFRAME_BUCKETS:
        matching = [p for p in projects if (timeframe_bucket(p.timeline) or ("",))[0] == key]
        rows.append(_row(f"time-{key}", f"Fits in {label.lower()}", "", matching))
    for major in MAJORS:
        if user.major and majors_match(user.major, (major,)):
            continue
        others = [p for p in projects if majors_match(major, p.associated_majors)]
        rows.append(_row(f"major-{major}", major, "", others))
    return [r for r in rows if r], notices


def _card_from_rec(card) -> dict:
    data = card.project.model_dump(mode="json")
    data["timeframe"] = timeframe_filter(card.project.timeline)
    data["hours"] = card.project.timeline.total_hours
    data["score"] = card.score
    return data


def _dashboard_for(user: NormalizedUser):
    ctx = get_context()
    projects = ctx.data.list_projects()
    rows, notices = build_rows(user, projects)
    welcome = session.pop("welcome", None)
    return render_template(
        "dashboard.html",
        user=user.model_dump(mode="json"),
        rows=rows,
        warnings=[n.model_dump() for n in notices],
        data_source=ctx.data_source,
        welcome=welcome,
    )


@pages.route("/dashboard")
def dashboard():
    user = current_user()
    if user is None:
        return redirect(url_for("pages.index", new=1))
    return _dashboard_for(user)


@pages.route("/dashboard/<user_id>")
def dashboard_for_user(user_id: str):
    user = get_context().data.get_user(user_id)
    if user is None:
        return jsonify(error="user not found"), 404
    return _dashboard_for(user)


# ---- project page ---------------------------------------------------------------------------

RESOURCE_GROUPS = (
    ("guide", "Getting started notes"),
    ("documentation", "Documentation"),
    ("tutorial", "Tutorials and videos"),
    ("research", "Research"),
    ("example", "Similar projects"),
    ("other", "More"),
)


@pages.route("/projects/<project_id>")
def project_page(project_id: str):
    ctx = get_context()
    project = ctx.data.get_project(project_id)
    if project is None:
        abort(404)
    groups = []
    for kind, label in RESOURCE_GROUPS:
        items = [r.model_dump(mode="json") for r in project.resources if r.kind == kind]
        if items:
            groups.append({"kind": kind, "label": label, "resources": items})
    steps = [s for s in (project.getting_started or "").splitlines() if s.strip()]
    user = current_user()
    return render_template(
        "project.html",
        project=project.model_dump(mode="json"),
        timeframe=timeframe_filter(project.timeline),
        hours=project.timeline.total_hours,
        steps=steps,
        materials=[m.model_dump(mode="json") for m in project.materials],
        resource_groups=groups,
        user=user.model_dump(mode="json") if user else None,
        data_source=ctx.data_source,
        serpapi_enabled=bool(ctx.settings.serpapi_api_key),
    )


# ---- forum ----------------------------------------------------------------------------------


def render_forum(error=None, status=200, form=None):
    conn = db.get_db()
    return render_template(
        "forum.html",
        posts=forum.list_posts(conn),
        users=forum.list_users(conn),
        projects=forum.list_projects(conn),
        limits={"title": forum.TITLE_MAX, "post": forum.POST_MAX, "comment": forum.COMMENT_MAX},
        error=error,
        form=form or {},
    ), status


@pages.route("/forum")
def show_forum():
    return render_forum()


@pages.route("/forum/posts", methods=["POST"])
def create_forum_post():
    f = request.form
    try:
        post_id = forum.create_post(
            db.get_db(), f.get("user_id"), f.get("title"), f.get("body"), f.get("project_id")
        )
    except forum.ForumError as exc:
        return render_forum(error=exc.message, status=exc.status, form=f)
    return redirect(url_for("pages.show_forum", _anchor=f"post-{post_id}"))


@pages.route("/forum/posts/<int:post_id>/comments", methods=["POST"])
def create_forum_comment(post_id):
    f = request.form
    try:
        forum.add_comment(db.get_db(), post_id, f.get("user_id"), f.get("body"))
    except forum.ForumError as exc:
        return render_forum(error=exc.message, status=exc.status, form=f)
    return redirect(url_for("pages.show_forum", _anchor=f"post-{post_id}"))

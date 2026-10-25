"""The Flask app: page routes, the SQLite database and the json_api /api/... routes.

Run from backend/:  ..\\.venv\\Scripts\\python app.py   (serves http://127.0.0.1:8000)
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for

REPO_ROOT = Path(__file__).resolve().parent.parent
for _name in ("env.txt", ".env"):
    load_dotenv(REPO_ROOT / _name, override=False)
# This app reads SQLite unless DATA_MODE=fake asks for json_api's offline fixtures.
os.environ.setdefault("DATA_MODE", "injected")

import db  # noqa: E402
import forum  # noqa: E402
from json_api import init_json_api  # noqa: E402
from json_api.config import Settings  # noqa: E402
from json_api.dependencies import get_context  # noqa: E402
from json_api.errors import AppError  # noqa: E402
from json_api.services import ranking  # noqa: E402
from sqlite_provider import SQLiteProjectDataProvider  # noqa: E402

settings = Settings.from_env()
app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
db.init_app(app)

data_provider = None if settings.data_mode == "fake" else SQLiteProjectDataProvider(db.get_db)
init_json_api(app, data_provider=data_provider, settings=settings)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard/<user_id>")
def display_user_dashboard(user_id):
    # IDs are strings: "1" and "2" are the seeded demo users ("fixture-ece" in fake mode).
    ctx = get_context()
    try:
        user = ctx.data.get_user(user_id)
        if user is None:
            return jsonify(error="user not found"), 404
        projects = ctx.data.list_projects()
        cards, warnings = ranking.recommend(user, projects, None, 3)
    except AppError as exc:
        return jsonify(error=exc.message, code=exc.code), exc.status

    return render_template(
        "dashboard.html",
        user=user.model_dump(mode="json"),
        recommendations=[c.model_dump(mode="json") for c in cards],
        warnings=[w.model_dump() for w in warnings],
        data_source=ctx.data_source,
    )

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


@app.route("/forum")
def show_forum():
    return render_forum()


@app.route("/forum/posts", methods=["POST"])
def create_forum_post():
    f = request.form
    try:
        post_id = forum.create_post(
            db.get_db(), f.get("user_id"), f.get("title"), f.get("body"), f.get("project_id")
        )
    except forum.ForumError as exc:
        return render_forum(error=exc.message, status=exc.status, form=f)
    return redirect(url_for("show_forum", _anchor=f"post-{post_id}"))


@app.route("/forum/posts/<int:post_id>/comments", methods=["POST"])
def create_forum_comment(post_id):
    f = request.form
    try:
        forum.add_comment(db.get_db(), post_id, f.get("user_id"), f.get("body"))
    except forum.ForumError as exc:
        return render_forum(error=exc.message, status=exc.status, form=f)
    return redirect(url_for("show_forum", _anchor=f"post-{post_id}"))


if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=True)

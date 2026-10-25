"""The Flask app: page routes, the SQLite database and the json_api /api/... routes.

Run from backend/:  ..\\.venv\\Scripts\\python app.py   (serves http://127.0.0.1:8000)
`flask --app app run` also works: Flask finds create_app() on its own.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Blueprint, Flask, jsonify, render_template

import db
from json_api import init_json_api
from json_api.config import Settings
from json_api.contracts import ProjectDataProvider
from json_api.dependencies import get_context
from json_api.errors import AppError
from json_api.llm.base import LLMProvider
from json_api.services import ranking
from sqlite_provider import SQLiteProjectDataProvider

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = REPO_ROOT / "frontend"

pages = Blueprint("pages", __name__)


def load_settings() -> Settings:
    """Settings from env.txt / .env / the environment. This app reads SQLite unless
    DATA_MODE=fake asks for json_api's offline fixtures."""
    for name in ("env.txt", ".env"):
        load_dotenv(REPO_ROOT / name, override=False)
    return Settings.from_env({"DATA_MODE": "injected", **os.environ})


def create_app(
    settings: Settings | None = None,
    config: dict | None = None,
    data_provider: ProjectDataProvider | None = None,
    llm_provider: LLMProvider | None = None,
) -> Flask:
    """Tests pass settings, config and providers; the dev server passes nothing."""
    settings = settings or load_settings()
    app = Flask(
        __name__,
        template_folder=str(FRONTEND / "templates"),
        static_folder=str(FRONTEND / "static"),
    )
    app.config.update(config or {})
    db.init_app(app)

    if data_provider is None and settings.data_mode != "fake":
        data_provider = SQLiteProjectDataProvider(db.get_db)
    init_json_api(app, data_provider=data_provider, llm_provider=llm_provider, settings=settings)
    app.register_blueprint(pages)
    return app


@pages.route("/")
def index():
    return render_template("index.html")


@pages.route("/forum")
def forum():
    return render_template("forum.html")


@pages.route("/dashboard/<user_id>")
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


if __name__ == "__main__":
    settings = load_settings()
    create_app(settings).run(host=settings.host, port=settings.port, debug=True)

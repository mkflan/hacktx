"""The Flask app: page routes, the SQLite database and the json_api /api/... routes.

Run from backend/:  ..\\.venv\\Scripts\\python app.py   (serves http://127.0.0.1:8000)
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify

REPO_ROOT = Path(__file__).resolve().parent.parent
for _name in ("env.txt", ".env"):
    load_dotenv(REPO_ROOT / _name, override=False)
# This app reads SQLite unless DATA_MODE=fake asks for json_api's offline fixtures.
os.environ.setdefault("DATA_MODE", "injected")

import db  # noqa: E402
from json_api import init_json_api  # noqa: E402
from json_api.config import Settings  # noqa: E402
from json_api.dependencies import get_context  # noqa: E402
from json_api.errors import AppError  # noqa: E402
from json_api.services import catalog, ranking  # noqa: E402
from sqlite_provider import SQLiteProjectDataProvider  # noqa: E402

settings = Settings.from_env()
app = Flask(__name__)
db.init_app(app)

data_provider = None if settings.data_mode == "fake" else SQLiteProjectDataProvider(db.get_db)
init_json_api(app, data_provider=data_provider, settings=settings)


@app.route("/")
def index():
    return jsonify(message="Hello from Flask!")


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
        facets = catalog.facets(projects)
    except AppError as exc:
        return jsonify(error=exc.message, code=exc.code), exc.status

    # TODO(frontend): replace this JSON with render_template("dashboard.html", ...) once the
    # page exists. These are the values the template would receive.
    return jsonify(
        user=user.model_dump(mode="json"),
        recommendations=[c.model_dump(mode="json") for c in cards],
        warnings=[w.model_dump() for w in warnings],
        facets={k: facets[k] for k in ("majors", "interests", "difficulties")},
        data_source=ctx.data_source,
    )


if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=True)

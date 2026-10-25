from flask import Flask, jsonify

import db
from json_api import init_json_api
from json_api.dependencies import get_context
from json_api.errors import AppError
from json_api.services import catalog, ranking

app = Flask(__name__)
db.init_app(app)

# TODO(database): pass data_provider=<your SQLite-backed ProjectDataProvider> here. Without one,
# json_api serves its FAKE fixture data (responses say data_source="fake") and the users table
# is not read. See docs/INTEGRATION.md.
init_json_api(app)


@app.route("/")
def index():
    return jsonify(message="Hello from Flask!")


@app.route("/dashboard/<user_id>")
def display_user_dashboard(user_id):
    # json_api IDs are opaque strings (fake mode uses "fixture-ece" and "fixture-cs").
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
    app.run(debug=True)

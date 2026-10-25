"""The Flask app: HTML pages, the SQLite database and the json_api /api/... routes.

Run from backend/:  ..\\.venv\\Scripts\\python app.py   (serves http://127.0.0.1:8000)
`flask --app app run` also works: Flask finds create_app() on its own.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

import db
from json_api import init_json_api
from json_api.config import Settings
from json_api.contracts import ProjectDataProvider
from json_api.llm.base import LLMProvider
from pages import pages
from serp import SerpApiClient
from sqlite_provider import SQLiteProjectDataProvider

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = REPO_ROOT / "frontend"


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
    app.secret_key = settings.secret_key
    db.init_app(app)

    if data_provider is None and settings.data_mode != "fake":
        data_provider = SQLiteProjectDataProvider(db.get_db)
    search_provider = (
        SerpApiClient(settings.serpapi_api_key, db.get_db) if settings.serpapi_api_key else None
    )
    init_json_api(
        app,
        data_provider=data_provider,
        llm_provider=llm_provider,
        search_provider=search_provider,
        settings=settings,
    )
    app.register_blueprint(pages)
    return app


if __name__ == "__main__":
    settings = load_settings()
    create_app(settings).run(host=settings.host, port=settings.port, debug=True)

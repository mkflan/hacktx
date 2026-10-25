import sqlite3
from pathlib import Path

from flask import current_app, g

DATABASE_PATH = Path(__file__).parent / "app.db"

SCHEMA = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
SEED = (Path(__file__).parent / "seed.sql").read_text(encoding="utf-8")
SCHEMA_VERSION = 3


def get_db():
    """Return the SQLite connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def apply_schema(db, seed=True):
    """Create the tables (and the demo rows) on any connection. Refuses an older app.db
    instead of silently running new queries against old tables."""
    version = db.execute("PRAGMA user_version").fetchone()[0]
    has_tables = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'users'"
    ).fetchone()
    if has_tables and version < SCHEMA_VERSION:
        raise RuntimeError(
            f"app.db uses schema version {version}, this code needs {SCHEMA_VERSION}. "
            "Delete backend/app.db (it only holds local dev data) and start again."
        )
    db.executescript(SCHEMA)
    if seed:
        db.executescript(SEED)
    db.commit()


def init_db():
    apply_schema(get_db(), seed=current_app.config["SEED_DEMO_DATA"])


def init_app(app):
    app.config.setdefault("DATABASE", str(DATABASE_PATH))
    app.config.setdefault("SEED_DEMO_DATA", True)
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

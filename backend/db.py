import sqlite3
from pathlib import Path

from flask import current_app, g

DATABASE_PATH = Path(__file__).parent / "app.db"

SCHEMA = (Path(__file__).parent / "schema.sql").read_text()

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


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


def init_app(app):
    app.config.setdefault("DATABASE", str(DATABASE_PATH))
    app.teardown_appcontext(close_db)
    
    with app.app_context():
        init_db()
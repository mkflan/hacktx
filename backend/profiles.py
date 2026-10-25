"""The landing-page profile form: validate it and create (or re-enter) a user. SQLite write
path, kept out of json_api/ like the other SQL modules."""

import re

from seed_data import DIFFICULTIES, MAJORS, TIMEFRAME_OPTIONS

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{2,40}$")
MAX_INTERESTS = 10
MAX_INTEREST_LEN = 40
TIMEFRAMES = {key: (label, hours) for key, label, hours in TIMEFRAME_OPTIONS}


class ProfileError(Exception):
    """A bad form submission; the message is safe to show to the student."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
        self.status = 400


def _getlist(form, key: str) -> list[str]:
    getlist = getattr(form, "getlist", None)
    if getlist is not None:
        return list(getlist(key))
    value = form.get(key, [])
    return list(value) if isinstance(value, list | tuple) else [value]


def parse_profile(form) -> dict:
    """Form fields -> a users row dict. Raises ProfileError with a human message."""
    username = (form.get("username") or "").strip()
    if not USERNAME_RE.match(username):
        raise ProfileError("Pick a username of 2-40 letters, numbers, dots, dashes or underscores.")

    major = (form.get("major") or "").strip()
    if major not in MAJORS:
        raise ProfileError("Choose your major from the list.")

    picked = [i.strip().lower() for i in _getlist(form, "interests") if i.strip()]
    extra = [i.strip().lower() for i in (form.get("other_interests") or "").split(",")]
    interests = list(dict.fromkeys(i for i in picked + extra if i))
    if not interests:
        raise ProfileError("Pick at least one interest.")
    if len(interests) > MAX_INTERESTS:
        raise ProfileError(f"Pick at most {MAX_INTERESTS} interests.")
    for interest in interests:
        if len(interest) > MAX_INTEREST_LEN or "," in interest:
            raise ProfileError("Each interest must be under 40 characters.")

    timeframe = form.get("timeframe") or ""
    if timeframe not in TIMEFRAMES:
        raise ProfileError("Choose how much time you have.")
    label, hours = TIMEFRAMES[timeframe]

    difficulty = (form.get("difficulty") or "").strip().lower() or None
    if difficulty is not None and difficulty not in DIFFICULTIES:
        raise ProfileError("Choose a difficulty from the list.")

    return {
        "username": username,
        "major": major,
        "interests": ", ".join(interests),
        "time_amount": float(hours),
        "time_raw": label,
        "difficulty": difficulty,
    }


def find_user_id(conn, username: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM users WHERE username = ? COLLATE NOCASE", (username,)
    ).fetchone()
    return None if row is None else row["id"]


def create_or_enter(conn, form) -> tuple[int, bool]:
    """Create the user from the form, or re-enter an existing username (the demo has no
    passwords). Returns (user_id, created)."""
    profile = parse_profile(form)
    existing = find_user_id(conn, profile["username"])
    if existing is not None:
        return existing, False
    cur = conn.execute(
        "INSERT INTO users (username, major, interests, time_amount, time_unit, time_raw, "
        "difficulty) VALUES (?, ?, ?, ?, 'total_hours', ?, ?)",
        (
            profile["username"],
            profile["major"],
            profile["interests"],
            profile["time_amount"],
            profile["time_raw"],
            profile["difficulty"],
        ),
    )
    conn.commit()
    return cur.lastrowid, True

"""Writes the authored demo data (seed_data/) into SQLite. Idempotent: fixed IDs and
INSERT OR IGNORE, so it runs on every start without duplicating rows.

Rows that scripts/enrich_catalog.py adds later (SerpApi resources, shop links) survive a
reseed because nothing here deletes.
"""

import json
import sqlite3

import seed_data

USERS = "INSERT OR IGNORE INTO users (id, username, major, interests, time_amount, time_unit, time_raw, difficulty) VALUES (?, ?, ?, ?, ?, 'total_hours', ?, ?)"  # fmt: skip
PROJECTS = "INSERT OR IGNORE INTO projects (id, slug, name, scope, majors, interests, timeline_amount, timeline_unit, timeline_raw, timeline_estimated_hours, difficulty, getting_started) VALUES (?, ?, ?, ?, ?, ?, ?, 'total_hours', ?, NULL, ?, ?)"  # fmt: skip
MATERIALS = "INSERT OR IGNORE INTO materials (project_id, position, name, quantity, purpose, estimated_cost_usd) VALUES (?, ?, ?, ?, ?, ?)"  # fmt: skip
RESOURCES = "INSERT OR IGNORE INTO resources (project_id, slug, title, url, kind, provider, topic_tags, content_excerpt, source, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'authored', '{}')"  # fmt: skip
POSTS = "INSERT OR IGNORE INTO posts (id, user_id, project_id, kind, title, body, majors, interests, difficulty, estimated_hours, starter_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"  # fmt: skip
COMMENTS = "INSERT OR IGNORE INTO comments (id, post_id, user_id, body, created_at) VALUES (?, ?, ?, ?, ?)"  # fmt: skip


def csv(items) -> str:
    return ", ".join(items)


def hours_label(hours: float) -> str:
    return f"{hours:g} total hours"


def seed_users(conn: sqlite3.Connection) -> None:
    for user_id, u in enumerate(seed_data.USERS, start=1):
        conn.execute(
            USERS,
            (
                user_id,
                u["username"],
                u["major"],
                csv(u["interests"]),
                u["hours"],
                u["time_raw"],
                u["difficulty"],
            ),
        )


def seed_projects(conn: sqlite3.Connection) -> None:
    for project_id, p in enumerate(seed_data.PROJECTS, start=1):
        conn.execute(
            PROJECTS,
            (
                project_id,
                p["slug"],
                p["name"],
                p["description"],
                csv(p["majors"]),
                csv(p["interests"]),
                p["hours"],
                hours_label(p["hours"]),
                p["difficulty"],
                p["getting_started"],
            ),
        )
        for position, m in enumerate(p["materials"], start=1):
            conn.execute(
                MATERIALS,
                (
                    project_id,
                    position,
                    m["name"],
                    m["quantity"],
                    m["purpose"],
                    m["estimated_cost_usd"],
                ),
            )
        for r in p["resources"]:
            conn.execute(
                RESOURCES,
                (
                    project_id,
                    r["slug"],
                    r["title"],
                    r["url"],
                    r["kind"],
                    r["provider"],
                    csv(r["tags"]),
                    r["excerpt"],
                ),
            )


def project_ids_by_slug(conn: sqlite3.Connection) -> dict[str, int]:
    return {row["slug"]: row["id"] for row in conn.execute("SELECT id, slug FROM projects")}


def user_ids_by_name(conn: sqlite3.Connection) -> dict[str, int]:
    return {row["username"]: row["id"] for row in conn.execute("SELECT id, username FROM users")}


# Forum discussion posts between the two demo users. Starters are seeded by seed_starters().
DISCUSSIONS = (
    (
        1, "alex_demo", "soil-moisture-monitor", "Soil sensor readings are noisy, any tips?",
        "I wired the analog moisture sensor to 3.3 V and the readings jump around by about 10%. "
        "Averaging helped a little. Has anyone calibrated theirs against a dry and a wet sample?",
        "2026-10-20 14:05:00",
    ),
    (
        2, "maya_demo", "vocab-spaced-repetition", "Looking for feedback on my flashcard scheduler",
        "My spaced-repetition app uses fixed intervals of 1, 3, 7 and 14 days and resets a card "
        "to day 1 when it is missed. Does that seem reasonable, or should I try something adaptive?",
        "2026-10-21 09:30:00",
    ),
    (
        3, "maya_demo", None, "Anyone want to team up on a data visualization project?",
        "I am a CS major interested in data visualization and sensors. If you have sensor data and "
        "want to chart it, let us talk.",
        "2026-10-22 18:45:00",
    ),
)  # fmt: skip

DISCUSSION_COMMENTS = (
    (
        1,
        1,
        "maya_demo",
        "Try taking the median of ten samples instead of the mean. It ignores the spikes.",
        "2026-10-20 16:20:00",
    ),  # fmt: skip
    (
        2,
        3,
        "alex_demo",
        "I have a week of soil sensor logs. Would love a chart of them.",
        "2026-10-23 08:10:00",
    ),  # fmt: skip
)


def seed_forum(conn: sqlite3.Connection) -> None:
    projects = project_ids_by_slug(conn)
    users = user_ids_by_name(conn)
    for post_id, author, slug, title, body, created in DISCUSSIONS:
        conn.execute(
            POSTS,
            (
                post_id,
                users[author],
                projects[slug] if slug else None,
                "discussion",
                title,
                body,
                "",
                "",
                None,
                None,
                None,
                created,
            ),
        )
    for comment_id, post_id, author, body, created in DISCUSSION_COMMENTS:
        conn.execute(COMMENTS, (comment_id, post_id, users[author], body, created))


def insert_starter(
    conn: sqlite3.Connection,
    *,
    post_id: int | None,
    user_id: int,
    project_id: int | None,
    title: str,
    body: str,
    majors,
    interests,
    difficulty: str | None,
    estimated_hours: float | None,
    starter: dict,
    created_at: str | None = None,
) -> int:
    """A forum 'starter': a generated project plan posted for others to pick up."""
    cur = conn.execute(
        POSTS
        if post_id is not None
        else POSTS.replace("(id, user_id", "(user_id").replace("VALUES (?, ?", "VALUES (?", 1),  # noqa: E501
        tuple(
            v
            for v in (
                post_id,
                user_id,
                project_id,
                "starter",
                title,
                body,
                csv(majors),
                csv(interests),
                difficulty,
                estimated_hours,
                json.dumps(starter, ensure_ascii=False),
                created_at,
            )
            if not (post_id is None and v is post_id)
        ),
    )
    return post_id if post_id is not None else cur.lastrowid


def seed_all(conn: sqlite3.Connection) -> None:
    seed_users(conn)
    seed_projects(conn)
    seed_forum(conn)
    conn.commit()

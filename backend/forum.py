"""Forum queries (posts, comments and project starters). Every function takes a connection so
tests can pass an in-memory database. Kept out of json_api/, which never opens SQLite."""

import json

from seed_data import DIFFICULTIES

TITLE_MAX = 120
POST_MAX = 2000
COMMENT_MAX = 1000
KINDS = ("discussion", "starter")

SORTS = {
    "newest": "p.created_at DESC, p.id DESC",
    "oldest": "p.created_at ASC, p.id ASC",
    "comments": "comment_count DESC, p.created_at DESC, p.id DESC",
    "hours": "p.estimated_hours IS NULL, p.estimated_hours ASC, p.created_at DESC",
    "difficulty": (
        "CASE p.difficulty WHEN 'beginner' THEN 0 WHEN 'intermediate' THEN 1 "
        "WHEN 'advanced' THEN 2 ELSE 3 END, p.created_at DESC"
    ),
}
SORT_LABELS = (
    ("newest", "Newest"),
    ("oldest", "Oldest"),
    ("comments", "Most discussed"),
    ("hours", "Fewest hours"),
    ("difficulty", "Easiest first"),
)

_SELECT = """
    SELECT p.id, p.kind, p.title, p.body, p.created_at, p.project_id, p.majors, p.interests,
           p.difficulty, p.estimated_hours, p.starter_json,
           u.id AS author_id, u.username AS author, u.major AS author_major,
           pr.name AS project_name,
           (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count
    FROM posts p
    JOIN users u ON u.id = p.user_id
    LEFT JOIN projects pr ON pr.id = p.project_id
"""


class ForumError(Exception):
    """A bad request: the message is safe to show to the user."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


def _clean(value, label: str, max_len: int) -> str:
    text = (value or "").strip()
    if not text:
        raise ForumError(f"{label} cannot be empty.")
    if len(text) > max_len:
        raise ForumError(f"{label} is too long (max {max_len} characters).")
    return text


def _split(text) -> list[str]:
    return [p.strip() for p in (text or "").split(",") if p.strip()]


def _user_id(conn, raw) -> int:
    try:
        user_id = int(raw)
    except TypeError, ValueError:
        raise ForumError("Choose who you are posting as.") from None
    if conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone() is None:
        raise ForumError("Unknown user.")
    return user_id


def list_projects(conn) -> list[dict]:
    rows = conn.execute("SELECT id, name FROM projects ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def _post(row) -> dict:
    post = dict(row)
    post["majors"] = _split(post["majors"])
    post["interests"] = _split(post["interests"])
    raw = post.pop("starter_json")
    post["starter"] = None
    if raw:
        try:
            post["starter"] = json.loads(raw)
        except ValueError:
            post["starter"] = None
    post["comments"] = []
    return post


def _attach_comments(conn, posts: list[dict]) -> list[dict]:
    if not posts:
        return posts
    by_id = {p["id"]: p for p in posts}
    marks = ", ".join("?" for _ in by_id)
    for r in conn.execute(
        f"""
        SELECT c.id, c.post_id, c.body, c.created_at, u.username AS author
        FROM comments c JOIN users u ON u.id = c.user_id
        WHERE c.post_id IN ({marks})
        ORDER BY c.created_at, c.id
        """,
        list(by_id),
    ):
        by_id[r["post_id"]]["comments"].append(dict(r))
    return posts


def list_posts(conn, *, q=None, kind=None, difficulty=None, sort="newest") -> list[dict]:
    """Posts with author, linked project, tags, starter plan and comments (oldest first).
    q searches title, body, tags, author and project name; sort is a key of SORTS."""
    where, params = [], []
    if q:
        like = f"%{q.strip()}%"
        where.append(
            "(p.title LIKE ? OR p.body LIKE ? OR p.majors LIKE ? OR p.interests LIKE ? "
            "OR u.username LIKE ? OR pr.name LIKE ?)"
        )
        params += [like] * 6
    if kind in KINDS:
        where.append("p.kind = ?")
        params.append(kind)
    if difficulty in DIFFICULTIES:
        where.append("p.difficulty = ?")
        params.append(difficulty)
    sql = _SELECT
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY " + SORTS.get(sort, SORTS["newest"])
    return _attach_comments(conn, [_post(r) for r in conn.execute(sql, params)])


def get_post(conn, post_id: int) -> dict | None:
    row = conn.execute(_SELECT + " WHERE p.id = ?", (post_id,)).fetchone()
    if row is None:
        return None
    return _attach_comments(conn, [_post(row)])[0]


def create_post(conn, user_id, title, body, project_id=None) -> int:
    uid = _user_id(conn, user_id)
    title = _clean(title, "Title", TITLE_MAX)
    body = _clean(body, "Post", POST_MAX)
    pid = None
    if project_id not in (None, ""):
        try:
            pid = int(project_id)
        except TypeError, ValueError:
            raise ForumError("Unknown project.") from None
        if conn.execute("SELECT 1 FROM projects WHERE id = ?", (pid,)).fetchone() is None:
            raise ForumError("Unknown project.")
    cur = conn.execute(
        "INSERT INTO posts (user_id, project_id, title, body) VALUES (?, ?, ?, ?)",
        (uid, pid, title, body),
    )
    conn.commit()
    return cur.lastrowid


def create_starter(conn, user_id, payload: dict, created_at: str | None = None) -> int:
    """Publish a generated ProjectPlan as a 'starter' post. payload = {plan, original_idea?,
    generation_mode?, web_results?} exactly as the chat page received it from the API."""
    uid = _user_id(conn, user_id)
    plan = payload.get("plan") if isinstance(payload, dict) else None
    if not isinstance(plan, dict) or not plan.get("name"):
        raise ForumError("That starter has no plan in it.")
    title = _clean(plan.get("name"), "Title", TITLE_MAX)
    summary = " ".join(str(plan.get("summary") or "").split())
    deliverable = " ".join(str(plan.get("deliverable") or "").split())
    body = _clean(
        (summary + (f"\n\nDeliverable: {deliverable}" if deliverable else ""))[:POST_MAX],
        "Post",
        POST_MAX,
    )
    difficulty = plan.get("difficulty")
    if difficulty not in DIFFICULTIES:
        difficulty = None
    hours = plan.get("estimated_total_hours")
    hours = float(hours) if isinstance(hours, int | float) and hours >= 0 else None
    columns = (
        "user_id, kind, title, body, majors, interests, difficulty, estimated_hours, starter_json"
    )
    values = [
        uid,
        "starter",
        title,
        body,
        ", ".join(str(m) for m in plan.get("associated_majors") or []),
        ", ".join(str(i) for i in plan.get("interests") or []),
        difficulty,
        hours,
        json.dumps(payload, ensure_ascii=False),
    ]
    if created_at:
        columns += ", created_at"
        values.append(created_at)
    marks = ", ".join("?" for _ in values)
    cur = conn.execute(f"INSERT INTO posts ({columns}) VALUES ({marks})", values)
    conn.commit()
    return cur.lastrowid


def add_comment(conn, post_id: int, user_id, body) -> int:
    if conn.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,)).fetchone() is None:
        raise ForumError("Post not found.", 404)
    uid = _user_id(conn, user_id)
    body = _clean(body, "Comment", COMMENT_MAX)
    cur = conn.execute(
        "INSERT INTO comments (post_id, user_id, body) VALUES (?, ?, ?)", (post_id, uid, body)
    )
    conn.commit()
    return cur.lastrowid

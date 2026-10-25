"""Forum queries (posts and comments). Every function takes a connection so tests can pass an
in-memory database. Kept out of json_api/, which never opens SQLite."""

TITLE_MAX = 120
POST_MAX = 2000
COMMENT_MAX = 1000


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


def _user_id(conn, raw) -> int:
    try:
        user_id = int(raw)
    except (TypeError, ValueError):
        raise ForumError("Choose who you are posting as.") from None
    if conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone() is None:
        raise ForumError("Unknown user.")
    return user_id


def list_users(conn) -> list[dict]:
    rows = conn.execute("SELECT id, username, major FROM users ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def list_projects(conn) -> list[dict]:
    rows = conn.execute("SELECT id, name FROM projects ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def list_posts(conn) -> list[dict]:
    """Newest first, each with its author, linked project and comments (oldest first)."""
    posts = [
        dict(r)
        for r in conn.execute(
            """
            SELECT p.id, p.title, p.body, p.created_at, p.project_id,
                   u.id AS author_id, u.username AS author, u.major AS author_major,
                   pr.name AS project_name
            FROM posts p
            JOIN users u ON u.id = p.user_id
            LEFT JOIN projects pr ON pr.id = p.project_id
            ORDER BY p.created_at DESC, p.id DESC
            """
        )
    ]
    by_id = {p["id"]: p for p in posts}
    for p in posts:
        p["comments"] = []
    for r in conn.execute(
        """
        SELECT c.id, c.post_id, c.body, c.created_at, u.username AS author
        FROM comments c JOIN users u ON u.id = c.user_id
        ORDER BY c.created_at, c.id
        """
    ):
        by_id[r["post_id"]]["comments"].append(dict(r))
    return posts


def create_post(conn, user_id, title, body, project_id=None) -> int:
    uid = _user_id(conn, user_id)
    title = _clean(title, "Title", TITLE_MAX)
    body = _clean(body, "Post", POST_MAX)
    pid = None
    if project_id not in (None, ""):
        try:
            pid = int(project_id)
        except (TypeError, ValueError):
            raise ForumError("Unknown project.") from None
        if conn.execute("SELECT 1 FROM projects WHERE id = ?", (pid,)).fetchone() is None:
            raise ForumError("Unknown project.")
    cur = conn.execute(
        "INSERT INTO posts (user_id, project_id, title, body) VALUES (?, ?, ?, ?)",
        (uid, pid, title, body),
    )
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

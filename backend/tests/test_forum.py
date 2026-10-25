"""Forum queries and the forum template against an in-memory database. No file, no network."""

from pathlib import Path

import pytest
from flask import Flask, render_template
from test_sqlite_provider import memory_db

import forum

TEMPLATES = Path(__file__).resolve().parents[2] / "frontend" / "templates"


@pytest.fixture
def conn():
    connection = memory_db()
    yield connection
    connection.close()


def test_seed_posts_are_listed_newest_first_with_comments(conn):
    posts = forum.list_posts(conn)
    assert [p["id"] for p in posts] == [3, 2, 1]
    assert posts[2]["author"] == "alex_demo"
    assert posts[2]["project_name"] == "Smart Soil Moisture Monitor"
    assert posts[0]["project_name"] is None
    assert [c["author"] for c in posts[2]["comments"]] == ["maya_demo"]


def test_create_post_and_comment(conn):
    post_id = forum.create_post(conn, "1", "  Hello  ", " My first post ", "2")
    first = forum.list_posts(conn)[0]
    assert first["id"] == post_id
    assert (first["title"], first["body"], first["project_id"]) == ("Hello", "My first post", 2)

    forum.add_comment(conn, post_id, "2", "Welcome!")
    assert forum.list_posts(conn)[0]["comments"][0]["body"] == "Welcome!"


@pytest.mark.parametrize(
    "args",
    [
        ("", "t", "b"),  # no user chosen
        ("abc", "t", "b"),
        ("99", "t", "b"),  # unknown user
        ("1", "   ", "b"),  # empty title
        ("1", "t", ""),  # empty body
        ("1", "x" * (forum.TITLE_MAX + 1), "b"),
        ("1", "t", "x" * (forum.POST_MAX + 1)),
        ("1", "t", "b", "999"),  # unknown project
        ("1", "t", "b", "nope"),
    ],
)
def test_create_post_rejects_bad_input(conn, args):
    with pytest.raises(forum.ForumError) as exc:
        forum.create_post(conn, *args)
    assert exc.value.status == 400
    assert len(forum.list_posts(conn)) == 3


def test_comment_on_missing_post_is_404_and_empty_comment_is_400(conn):
    with pytest.raises(forum.ForumError) as exc:
        forum.add_comment(conn, 999, "1", "hi")
    assert exc.value.status == 404
    with pytest.raises(forum.ForumError) as exc:
        forum.add_comment(conn, 1, "1", "  ")
    assert exc.value.status == 400


def test_seed_is_idempotent_for_the_forum(conn):
    import db

    db.apply_schema(conn)
    assert len(forum.list_posts(conn)) == 3


def test_template_renders_posts_and_escapes_html(conn):
    forum.create_post(conn, "1", "<script>alert(1)</script>", "<b>bold</b>")
    app = Flask(__name__, template_folder=str(TEMPLATES))
    with app.test_request_context():
        html = render_template(
            "forum.html",
            posts=forum.list_posts(conn),
            users=forum.list_users(conn),
            projects=forum.list_projects(conn),
            limits={"title": 120, "post": 2000, "comment": 1000},
            error="Title cannot be empty.",
            form={},
        )
    assert "Soil sensor readings are noisy" in html
    assert "Title cannot be empty." in html
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "Freetail" not in html

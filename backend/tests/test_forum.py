"""Forum queries and the forum template against an in-memory database. No file, no network."""

from pathlib import Path

import pytest
from flask import Flask, render_template

import db
import forum
import seed_data

SEEDED_POSTS = 3 + len(seed_data.STARTERS)  # three discussions plus the community starters

TEMPLATES = Path(__file__).resolve().parents[2] / "frontend" / "templates"


@pytest.fixture
def conn():
    connection = db.connect_memory()
    yield connection
    connection.close()


def test_seed_posts_are_listed_newest_first_with_comments(conn):
    posts = forum.list_posts(conn, kind="discussion")
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
    assert len(forum.list_posts(conn)) == SEEDED_POSTS


def test_comment_on_missing_post_is_404_and_empty_comment_is_400(conn):
    with pytest.raises(forum.ForumError) as exc:
        forum.add_comment(conn, 999, "1", "hi")
    assert exc.value.status == 404
    with pytest.raises(forum.ForumError) as exc:
        forum.add_comment(conn, 1, "1", "  ")
    assert exc.value.status == 400


def test_seed_is_idempotent_for_the_forum(conn):
    db.apply_schema(conn)
    assert len(forum.list_posts(conn)) == SEEDED_POSTS


def test_template_renders_posts_and_escapes_html(conn):
    forum.create_post(conn, "1", "<script>alert(1)</script>", "<b>bold</b>")
    app = Flask(__name__, template_folder=str(TEMPLATES))
    app.jinja_env.filters["hours"] = lambda v: f"{v:g}"
    with app.test_request_context():
        html = render_template(
            "forum.html",
            posts=forum.list_posts(conn),
            filters={"q": "", "kind": "", "difficulty": "", "sort": "newest"},
            sorts=forum.SORT_LABELS,
            users=forum.list_users(conn),
            projects=forum.list_projects(conn),
            limits={"title": 120, "post": 2000, "comment": 1000},
            error="Title cannot be empty.",
            form={},
            current_user=None,
            demo_users=[],
        )
    assert "Soil sensor readings are noisy" in html
    assert "Title cannot be empty." in html
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "Freetail" not in html


def test_search_filters_and_sorts(conn):
    assert [p["id"] for p in forum.list_posts(conn, q="flashcard")] == [2]
    assert [p["id"] for p in forum.list_posts(conn, q="maya_demo")] == [3, 2]
    assert [p["id"] for p in forum.list_posts(conn, q="Soil Moisture")] == [1]  # project name
    oldest = [p["id"] for p in forum.list_posts(conn, sort="oldest")]
    assert oldest[0] == 101 and oldest[-1] == 3  # first seeded starter ... newest discussion
    by_comments = forum.list_posts(conn, sort="comments")
    assert by_comments[0]["comment_count"] >= by_comments[-1]["comment_count"]
    starters = forum.list_posts(conn, kind="starter")
    assert len(starters) == len(seed_data.STARTERS)
    assert all(p["starter"]["plan"]["milestones"] for p in starters)
    assert [p["id"] for p in forum.list_posts(conn, kind="discussion")] == [3, 2, 1]
    assert forum.list_posts(conn, q="nothing matches this") == []
    assert forum.list_posts(conn, sort="not-a-sort")[0]["id"] == 3  # falls back to newest


def test_create_starter_and_read_it_back(conn):
    plan = {
        "name": "Spanish Verb Quiz App",
        "summary": "A daily quiz with a streak counter.",
        "deliverable": "A web app that quizzes 20 verbs a day.",
        "associated_majors": ["Computer Science"],
        "interests": ["language learning", "web apps"],
        "difficulty": "intermediate",
        "estimated_total_hours": 30,
        "milestones": [{"title": "Set up", "objective": "Repo and page", "estimated_hours": 5}],
    }
    payload = {"plan": plan, "original_idea": "quiz app", "generation_mode": "mock"}
    post_id = forum.create_starter(conn, "2", payload, created_at="2026-10-25 09:00:00")
    post = forum.get_post(conn, post_id)
    assert post["kind"] == "starter" and post["title"] == "Spanish Verb Quiz App"
    assert post["body"].startswith("A daily quiz") and "Deliverable:" in post["body"]
    assert post["majors"] == ["Computer Science"]
    assert post["interests"] == ["language learning", "web apps"]
    assert (post["difficulty"], post["estimated_hours"]) == ("intermediate", 30.0)
    assert post["starter"]["plan"]["milestones"][0]["title"] == "Set up"
    assert post["comment_count"] == 0 and post["comments"] == []
    assert forum.list_posts(conn, kind="starter")[0]["id"] == post_id  # newest starter first
    assert post_id in [p["id"] for p in forum.list_posts(conn, difficulty="intermediate")]
    hours = [p["estimated_hours"] for p in forum.list_posts(conn, sort="hours")]
    known = [h for h in hours if h is not None]
    assert known == sorted(known) and hours[-1] is None  # fewest hours first, unknown last
    assert forum.get_post(conn, 999) is None

    with pytest.raises(forum.ForumError, match="no plan"):
        forum.create_starter(conn, "2", {"plan": "not a dict"})
    with pytest.raises(forum.ForumError, match="posting as"):
        forum.create_starter(conn, "", payload)

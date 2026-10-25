"""The landing-form write path: validation and create-or-enter against an in-memory database."""

import pytest
from werkzeug.datastructures import MultiDict

import db
import profiles

GOOD = MultiDict(
    [
        ("username", "  Sam.Builds-2 "),
        ("major", "Mechanical Engineering"),
        ("interests", "3d printing"),
        ("interests", "Robotics"),
        ("other_interests", "kites, 3D Printing, "),
        ("timeframe", "two_weeks"),
        ("difficulty", "beginner"),
    ]
)


@pytest.fixture
def conn():
    connection = db.connect_memory()
    yield connection
    connection.close()


def test_parse_profile_normalizes_and_deduplicates():
    row = profiles.parse_profile(GOOD)
    assert row["username"] == "Sam.Builds-2"
    assert row["interests"] == "3d printing, robotics, kites"
    assert row["time_amount"] == 25 and "Two weeks" in row["time_raw"]
    assert row["difficulty"] == "beginner"


def test_difficulty_is_optional():
    form = MultiDict(GOOD)
    form["difficulty"] = ""
    assert profiles.parse_profile(form)["difficulty"] is None


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("username", "x", "username"),
        ("username", "has space", "username"),
        ("major", "Astrology", "major"),
        ("timeframe", "forever", "time"),
        ("difficulty", "wizard", "difficulty"),
        ("other_interests", "x" * 50, "40 characters"),
    ],
)
def test_parse_profile_rejects_bad_fields(field, value, message):
    form = MultiDict(GOOD)
    form[field] = value
    with pytest.raises(profiles.ProfileError) as exc:
        profiles.parse_profile(form)
    assert message in exc.value.message


def test_no_interests_is_rejected():
    form = MultiDict([(k, v) for k, v in GOOD.items(multi=True) if k != "interests"])
    form["other_interests"] = " , "
    with pytest.raises(profiles.ProfileError, match="interest"):
        profiles.parse_profile(form)


def test_create_then_enter_again(conn):
    user_id, created = profiles.create_or_enter(conn, GOOD)
    assert created and user_id > 2
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    assert row["username"] == "Sam.Builds-2" and row["time_unit"] == "total_hours"
    assert row["difficulty"] == "beginner"

    again = MultiDict(GOOD)
    again["username"] = "sam.builds-2"  # different case, same student
    same_id, created_again = profiles.create_or_enter(conn, again)
    assert (same_id, created_again) == (user_id, False)
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 11

"""SQLite-backed ProjectDataProvider: reads the tables in schema.sql and maps each row into
json_api's DTOs. Read-only. It lives outside json_api/ so that package never imports sqlite3.

connect is any zero-argument function returning a connection with row_factory=sqlite3.Row:
db.get_db in the Flask app (one connection per request), or a fixed in-memory one in tests.
"""

import json
import sqlite3
from collections.abc import Callable, Iterable, Mapping

from json_api.contracts import Material, NormalizedProject, NormalizedUser, Resource, TimeValue

_USER_COLUMNS = "id, username, major, interests, time_amount, time_unit, time_raw, difficulty"
_PROJECT_COLUMNS = (
    "id, slug, name, scope, majors, interests, timeline_amount, timeline_unit, timeline_raw, "
    "timeline_estimated_hours, difficulty, getting_started"
)
_RESOURCE_COLUMNS = (
    "project_id, slug, title, url, kind, provider, topic_tags, content_excerpt, source, "
    "thumbnail_url, metadata_json"
)
_MATERIAL_COLUMNS = (
    "project_id, position, name, quantity, purpose, estimated_cost_usd, shop_url, shop_source, "
    "price_usd"
)


def split_list(text: str | None) -> tuple[str, ...]:
    """'sensors, plants,,IoT ' -> ('sensors', 'plants', 'IoT'), duplicates dropped."""
    return tuple(dict.fromkeys(p.strip() for p in (text or "").split(",") if p.strip()))


def _row_id(value: str) -> int | None:
    """API IDs are strings; SQLite IDs are integers. Anything else is simply not found."""
    return int(value) if value.isdecimal() else None


def user_from_row(row: Mapping) -> NormalizedUser:
    return NormalizedUser(
        id=row["id"],
        username=row["username"],
        major=row["major"] or "",
        interests=split_list(row["interests"]),
        time_commitment=TimeValue(
            amount=row["time_amount"], unit=row["time_unit"] or "unknown", raw=row["time_raw"]
        ),
        skill_level=row["difficulty"],
    )


def resource_from_row(row: Mapping) -> Resource:
    try:
        metadata = json.loads(row["metadata_json"] or "{}")
    except TypeError, ValueError:
        metadata = {}
    return Resource(
        id=f"{row['project_id']}/{row['slug']}",
        title=row["title"],
        url=row["url"],
        kind=row["kind"] or "other",
        provider=row["provider"],
        topic_tags=split_list(row["topic_tags"]),
        content_excerpt=row["content_excerpt"],
        source=row["source"] or "authored",
        thumbnail_url=row["thumbnail_url"],
        metadata={k: str(v) for k, v in metadata.items()} if isinstance(metadata, dict) else {},
    )


def material_from_row(row: Mapping) -> Material:
    return Material(
        name=row["name"],
        quantity=row["quantity"],
        purpose=row["purpose"],
        estimated_cost_usd=row["estimated_cost_usd"],
        shop_url=row["shop_url"],
        shop_source=row["shop_source"],
        price_usd=row["price_usd"],
    )


def project_from_row(
    row: Mapping, resource_rows: Iterable[Mapping] = (), material_rows: Iterable[Mapping] = ()
) -> NormalizedProject:
    return NormalizedProject(
        id=row["id"],
        name=row["name"],
        description=row["scope"],
        associated_majors=split_list(row["majors"]),
        interests=split_list(row["interests"]),
        timeline=TimeValue(
            amount=row["timeline_amount"],
            unit=row["timeline_unit"] or "unknown",
            raw=row["timeline_raw"],
            estimated_total_hours=row["timeline_estimated_hours"],
        ),
        difficulty=row["difficulty"],
        getting_started=row["getting_started"],
        resources=tuple(resource_from_row(r) for r in resource_rows),
        materials=tuple(material_from_row(m) for m in material_rows),
    )


class SQLiteProjectDataProvider:
    data_source = "sqlite"

    def __init__(self, connect: Callable[[], sqlite3.Connection]) -> None:
        self._connect = connect

    def list_users(self) -> list[NormalizedUser]:
        rows = self._connect().execute(f"SELECT {_USER_COLUMNS} FROM users ORDER BY id")
        return [user_from_row(r) for r in rows]

    def get_user(self, user_id: str) -> NormalizedUser | None:
        row_id = _row_id(user_id)
        if row_id is None:
            return None
        row = (
            self._connect()
            .execute(f"SELECT {_USER_COLUMNS} FROM users WHERE id = ?", (row_id,))
            .fetchone()
        )
        return None if row is None else user_from_row(row)

    def list_projects(self) -> list[NormalizedProject]:
        db = self._connect()
        resources: dict[int, list] = {}
        for r in db.execute(
            f"SELECT {_RESOURCE_COLUMNS} FROM resources ORDER BY project_id, rowid"
        ):
            resources.setdefault(r["project_id"], []).append(r)
        materials: dict[int, list] = {}
        for m in db.execute(
            f"SELECT {_MATERIAL_COLUMNS} FROM materials ORDER BY project_id, position"
        ):
            materials.setdefault(m["project_id"], []).append(m)
        rows = db.execute(f"SELECT {_PROJECT_COLUMNS} FROM projects ORDER BY id")
        return [
            project_from_row(r, resources.get(r["id"], ()), materials.get(r["id"], ()))
            for r in rows
        ]

    def get_project(self, project_id: str) -> NormalizedProject | None:
        row_id = _row_id(project_id)
        if row_id is None:
            return None
        db = self._connect()
        row = db.execute(
            f"SELECT {_PROJECT_COLUMNS} FROM projects WHERE id = ?", (row_id,)
        ).fetchone()
        if row is None:
            return None
        resource_rows = db.execute(
            f"SELECT {_RESOURCE_COLUMNS} FROM resources WHERE project_id = ? ORDER BY rowid",
            (row_id,),
        ).fetchall()
        material_rows = db.execute(
            f"SELECT {_MATERIAL_COLUMNS} FROM materials WHERE project_id = ? ORDER BY position",
            (row_id,),
        ).fetchall()
        return project_from_row(row, resource_rows, material_rows)

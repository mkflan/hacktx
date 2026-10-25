"""Attach real web resources and shop links to catalog projects (SQLite writes).

Used live by the "Dig deeper" button and offline by scripts/enrich_catalog.py. Everything
written here came back from a search engine and is labeled source='serpapi:<engine>'.
"""

import sqlite3

from json_api.contracts import NormalizedProject, Resource
from json_api.search import SearchProvider, offers_from, project_queries, resources_from

INSERT_RESOURCE = (
    "INSERT OR IGNORE INTO resources (project_id, slug, title, url, kind, provider, topic_tags, "
    "content_excerpt, source, thumbnail_url, metadata_json, fetched_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
)
UPDATE_MATERIAL = (
    "UPDATE materials SET shop_url = ?, shop_source = ?, price_usd = ?, fetched_at = "
    "CURRENT_TIMESTAMP WHERE project_id = ? AND position = ?"
)
DIG_ENGINES = ("youtube", "google")
RESULTS_PER_ENGINE = 4


def _project_id(project: NormalizedProject) -> int:
    return int(project.id)


def save_resources(
    conn: sqlite3.Connection, project: NormalizedProject, found: list[Resource]
) -> int:
    """Insert resources found for the project; returns how many were new."""
    import json

    new = 0
    for r in found:
        slug = r.id.split("/", 1)[1]
        cur = conn.execute(
            INSERT_RESOURCE,
            (
                _project_id(project),
                slug,
                r.title,
                r.url,
                r.kind,
                r.provider,
                ", ".join(r.topic_tags),
                r.content_excerpt,
                r.source,
                r.thumbnail_url,
                json.dumps(r.metadata),
            ),
        )
        new += cur.rowcount
    conn.commit()
    return new


def dig_project(
    conn: sqlite3.Connection,
    search: SearchProvider,
    project: NormalizedProject,
    engines: tuple[str, ...] = DIG_ENGINES,
) -> tuple[list[Resource], int]:
    """Search the web for the project and store what comes back. Returns (found, new_count)."""
    queries = project_queries(project)
    found: list[Resource] = []
    for engine in engines:
        payload = search.search(engine, queries[engine])
        found += resources_from(
            engine,
            payload,
            id_prefix=project.id,
            tags=project.interests[:3],
            limit=RESULTS_PER_ENGINE,
        )
    return found, save_resources(conn, project, found)


def shop_materials(
    conn: sqlite3.Connection,
    search: SearchProvider,
    project: NormalizedProject,
    *,
    max_items: int = 3,
) -> int:
    """Look up where to buy the first few purchasable materials (cost > 0, no link yet)."""
    looked_up = 0
    for position, material in enumerate(project.materials, start=1):
        if looked_up >= max_items:
            break
        if material.shop_url or not material.estimated_cost_usd:
            continue
        offers = offers_from(search.search("google_shopping", material.name), limit=1)
        if not offers:
            continue
        offer = offers[0]
        conn.execute(
            UPDATE_MATERIAL,
            (offer["url"], offer["source"], offer["price_usd"], _project_id(project), position),
        )
        looked_up += 1
    conn.commit()
    return looked_up

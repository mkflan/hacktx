"""Fill the catalog with real web resources and shop links through SerpApi, inside a budget.

Run from the repo root with the venv:
    .venv\\Scripts\\python scripts\\enrich_catalog.py --max-searches 20
    .venv\\Scripts\\python scripts\\enrich_catalog.py --dry-run          # show the plan, no calls

Order: the projects recommended to the two demo students come first, so the pages the judges
see are the richest; then every other project by id. Per project: YouTube tutorials, a Google
documentation search, Google Scholar for intermediate and advanced projects, and one Google
Shopping lookup for the first purchasable material. Every answer is cached in serp_cache, so
re-running never pays for the same query twice; stop and restart whenever you like.

Cost: up to 4 SerpApi searches per project that is not cached yet (YouTube, Google, Scholar
for non-beginner projects, one Shopping lookup). The run prints the account balance first and
never spends more than --max-searches (default 20). Use --dry-run to see the plan for free.
"""

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "env.txt")
load_dotenv(ROOT / ".env")

import db  # noqa: E402
import enrich  # noqa: E402
import serp  # noqa: E402
from json_api.search import SearchError, project_queries  # noqa: E402
from json_api.services import ranking  # noqa: E402
from sqlite_provider import SQLiteProjectDataProvider  # noqa: E402


def priority_order(provider):
    projects = provider.list_projects()
    by_id = {p.id: p for p in projects}
    ordered, seen = [], set()
    for user in provider.list_users()[:2]:  # the two scripted demo students
        cards, _ = ranking.recommend(user, projects, None, 12)
        for card in cards:
            if card.project.id not in seen:
                seen.add(card.project.id)
                ordered.append(by_id[card.project.id])
    ordered += [p for p in projects if p.id not in seen]
    return ordered


def engines_for(project):
    engines = ["youtube", "google"]
    if project.difficulty != "beginner":
        engines.append("google_scholar")
    return engines


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--max-searches", type=int, default=20, help="live SerpApi calls allowed in this run"
    )
    parser.add_argument("--db", default=str(ROOT / "backend" / "app.db"))
    parser.add_argument("--no-shopping", action="store_true", help="skip Google Shopping lookups")
    parser.add_argument("--dry-run", action="store_true", help="print the plan; make no calls")
    parser.add_argument(
        "--export",
        action="store_true",
        help="after the run, write backend/serp_cache.json (the committed offline snapshot)",
    )
    parser.add_argument(
        "--export-only", action="store_true", help="only write the snapshot; search nothing"
    )
    args = parser.parse_args()

    conn = db.connect(args.db)
    db.apply_schema(conn)
    snapshot = ROOT / "backend" / "serp_cache.json"
    if args.export_only:
        print(f"exported {serp.export_cache(conn, snapshot)} cached queries to {snapshot}")
        return 0

    key = os.environ.get("SERPAPI_API_KEY", "").strip()
    if not key and not args.dry_run:
        print("SERPAPI_API_KEY is not set. Put it in env.txt (see env.example.txt).")
        return 2
    provider = SQLiteProjectDataProvider(lambda: conn)
    client = serp.SerpApiClient(key or "dry-run", lambda: conn, max_searches=args.max_searches)
    before = Counter(r["source"] for r in conn.execute("SELECT source FROM resources"))
    print(f"cache: {serp.cache_size(conn)} queries | resources before: {dict(before)}")
    if not args.dry_run:
        try:
            balance = client.account()
            print(
                f"SerpApi: {balance['searches_left']} searches left "
                f"({balance['used']} used this month); this run spends at most {args.max_searches}"
            )
        except SearchError as exc:
            print(f"SerpApi balance unknown: {exc.message}")

    for project in priority_order(provider):
        engines = engines_for(project)
        queries = project_queries(project)
        cached = [e for e in engines if client.cached(e, queries[e]) is not None]
        live = [e for e in engines if e not in cached]
        shop = None
        if not args.no_shopping:
            shop = next(
                (m for m in project.materials if m.estimated_cost_usd and not m.shop_url), None
            )
        if args.dry_run:
            print(
                f"[{project.id:>2}] {project.name[:48]:48} live={live} cached={cached}"
                + (f" shop='{shop.name[:30]}'" if shop else "")
            )
            continue
        try:
            found, new = enrich.dig_project(conn, client, project, engines=tuple(engines))
            shopped = enrich.shop_materials(conn, client, project, max_items=1) if shop else 0
        except SearchError as exc:
            print(f"[{project.id:>2}] {project.name[:48]:48} stopped: {exc.message}")
            if "budget" in exc.message:
                break
            continue
        print(
            f"[{project.id:>2}] {project.name[:48]:48} +{new} resources"
            f"{' +shop' if shopped else ''} | live calls so far: {client.calls}"
        )

    after = Counter(r["source"] for r in conn.execute("SELECT source FROM resources"))
    shops = conn.execute("SELECT COUNT(*) FROM materials WHERE shop_url IS NOT NULL").fetchone()[0]
    print(
        f"done: {client.calls} live searches this run | cache: {serp.cache_size(conn)} queries | "
        f"resources: {dict(after)} | materials with shop links: {shops}"
    )
    if args.export:
        print(f"exported {serp.export_cache(conn, snapshot)} cached queries to {snapshot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

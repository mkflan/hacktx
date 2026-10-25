"""SerpApi client with a SQLite cache (the serp_cache table). Implements json_api's
SearchProvider. A query is paid for once; every repeat is served from the cache, so the demo
runs offline once it has been warmed and the free plan's quota is not burned twice."""

import json
import logging
import sqlite3
from collections.abc import Callable

import httpx

from json_api.search import ENGINES, SearchError, clean_query

logger = logging.getLogger("serp")
BASE_URL = "https://serpapi.com/search.json"
ACCOUNT_URL = "https://serpapi.com/account.json"
DEFAULT_TIMEOUT = 25.0


class SerpApiClient:
    enabled = True

    def __init__(
        self,
        api_key: str,
        connect: Callable[[], sqlite3.Connection],
        *,
        max_searches: int | None = None,
        http: httpx.Client | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("SerpApiClient needs an API key")
        self._key = api_key
        self._connect = connect
        self._max = max_searches
        self._http = http or httpx.Client(timeout=DEFAULT_TIMEOUT)
        self.calls = 0  # live searches made by this client (cache hits do not count)

    def cached(self, engine: str, query: str) -> dict | None:
        row = (
            self._connect()
            .execute(
                "SELECT response_json FROM serp_cache WHERE engine = ? AND query = ?",
                (engine, clean_query(query)),
            )
            .fetchone()
        )
        return None if row is None else json.loads(row[0])

    def account(self) -> dict:
        """Searches left on the plan. SerpApi does not count this call as a search.
        Returns {searches_left (plan + extra credits), plan_searches_left, used (this month)}."""
        try:
            response = self._http.get(ACCOUNT_URL, params={"api_key": self._key})
        except httpx.HTTPError as exc:
            raise SearchError(f"Could not reach SerpApi ({type(exc).__name__}).") from exc
        if response.status_code != 200:
            raise SearchError(f"SerpApi answered HTTP {response.status_code}.")
        data = response.json()
        plan_left = int(data.get("plan_searches_left") or 0)
        total_left = data.get("total_searches_left")
        if total_left is None:
            total_left = plan_left + int(data.get("extra_credits") or 0)
        return {
            "searches_left": int(total_left),
            "plan_searches_left": plan_left,
            "used": int(data.get("this_month_usage") or 0),
        }

    def search(self, engine: str, query: str) -> dict:
        if engine not in ENGINES:
            raise SearchError(f"Unknown search engine {engine!r}.")
        query = clean_query(query)
        hit = self.cached(engine, query)
        if hit is not None:
            return hit
        if self._max is not None and self.calls >= self._max:
            raise SearchError("The search budget for this run is used up.")

        params = {"engine": engine, "api_key": self._key, ENGINES[engine]: query, "hl": "en"}
        if engine != "youtube":
            params["gl"] = "us"
        try:
            response = self._http.get(BASE_URL, params=params)
        except httpx.HTTPError as exc:
            # Never log the request URL: it carries the key.
            raise SearchError(f"Could not reach SerpApi ({type(exc).__name__}).") from exc
        if response.status_code != 200:
            raise SearchError(f"SerpApi answered HTTP {response.status_code}.")
        payload = response.json()
        error = str(payload.get("error") or "")
        if error and "hasn't returned any results" not in error:
            raise SearchError(f"SerpApi: {error[:200]}")
        # "No results" is a valid, cacheable answer: the conversions simply yield nothing.

        self.calls += 1
        conn = self._connect()
        conn.execute(
            "INSERT OR REPLACE INTO serp_cache (engine, query, response_json) VALUES (?, ?, ?)",
            (engine, query, json.dumps(payload)),
        )
        conn.commit()
        logger.info("SerpApi %s search #%d cached: %s", engine, self.calls, query)
        return payload


def cache_size(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM serp_cache").fetchone()[0]


class CacheOnlySearch:
    """Serves only what serp_cache already holds. Used to rebuild resources offline from the
    committed cache snapshot; never spends a search."""

    enabled = True

    def __init__(self, connect: Callable[[], sqlite3.Connection]) -> None:
        self._connect = connect

    def search(self, engine: str, query: str) -> dict:
        row = (
            self._connect()
            .execute(
                "SELECT response_json FROM serp_cache WHERE engine = ? AND query = ?",
                (engine, clean_query(query)),
            )
            .fetchone()
        )
        if row is None:
            raise SearchError(f"Not in the offline cache: {engine} {query!r}.")
        return json.loads(row[0])


# Only the fields the conversions read survive an export; full SerpApi payloads are large.
_KEEP = {
    "youtube": (
        "video_results",
        (
            "title",
            "link",
            "thumbnail",
            "channel",
            "published_date",
            "length",
            "views",
            "description",
        ),
    ),  # noqa: E501
    "google": ("organic_results", ("title", "link", "snippet", "source", "displayed_link")),
    "google_scholar": (
        "organic_results",
        ("title", "link", "snippet", "publication_info", "inline_links"),
    ),  # noqa: E501
    "google_shopping": (
        "shopping_results",
        ("title", "link", "product_link", "price", "extracted_price", "source", "thumbnail"),
    ),  # noqa: E501
}


def trim_payload(engine: str, payload: dict, limit: int = 10) -> dict:
    key, fields = _KEEP[engine]
    items = []
    for item in (payload.get(key) or [])[:limit]:
        kept = {f: item[f] for f in fields if f in item}
        if "description" in kept and isinstance(kept["description"], str):
            kept["description"] = kept["description"][:400]
        items.append(kept)
    trimmed = {key: items}
    if payload.get("error"):
        trimmed["error"] = str(payload["error"])[:200]
    return trimmed


def export_cache(conn: sqlite3.Connection, path) -> int:
    """Write serp_cache to a JSON file (trimmed). Returns the number of queries exported."""
    rows = conn.execute(
        "SELECT engine, query, response_json FROM serp_cache ORDER BY engine, query"
    )
    entries = [
        {"engine": engine, "query": query, "response": trim_payload(engine, json.loads(raw))}
        for engine, query, raw in rows
        if engine in _KEEP
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=0)
    return len(entries)


def import_cache(conn: sqlite3.Connection, path) -> int:
    """Load an exported snapshot into serp_cache without overwriting newer live answers."""
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    for e in entries:
        conn.execute(
            "INSERT OR IGNORE INTO serp_cache (engine, query, response_json) VALUES (?, ?, ?)",
            (e["engine"], e["query"], json.dumps(e["response"])),
        )
    conn.commit()
    return len(entries)

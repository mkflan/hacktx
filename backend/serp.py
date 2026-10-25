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

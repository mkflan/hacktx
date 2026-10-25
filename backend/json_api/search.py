"""Web search as an injectable provider, plus pure conversions of SerpApi payloads into
Resource records and shopping offers.

json_api never calls SerpApi itself: backend/serp.py implements SearchProvider with an HTTP
client and a SQLite cache and is injected through init_json_api(). Everything a search returns
is labeled source="serpapi:<engine>" and stays provided_unverified: a search hit is not a
content check, and the model may only link to URLs that came back from one.
"""

import hashlib
from typing import Any, Protocol, runtime_checkable
from urllib.parse import urlparse

from .contracts import NormalizedProject, Resource

# SerpApi engine -> the name of its query parameter.
ENGINES: dict[str, str] = {
    "youtube": "search_query",
    "google": "q",
    "google_scholar": "q",
    "google_shopping": "q",
}
MAX_QUERY_CHARS = 200


class SearchError(Exception):
    """The search could not run (no key, budget spent, network, SerpApi error)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@runtime_checkable
class SearchProvider(Protocol):
    enabled: bool

    def search(self, engine: str, query: str) -> dict:
        """Raw SerpApi JSON for engine+query (cached by the implementation). Raises SearchError."""
        ...


class DisabledSearch:
    """Installed when SERPAPI_API_KEY is not set: every search fails loudly, nothing is faked."""

    enabled = False

    def search(self, engine: str, query: str) -> dict:
        raise SearchError("Web search is not configured on this server (SERPAPI_API_KEY).")


def clean_query(query: str) -> str:
    return " ".join(query.split())[:MAX_QUERY_CHARS]


def short_query(text: str, words: int = 8) -> str:
    """The first few words of a sentence, for engines (YouTube) that return nothing for long
    natural-language queries."""
    return clean_query(" ".join(text.split()[:words]).strip(" .,;:!?"))


def _slug(engine: str, url: str) -> str:
    return f"{engine}-{hashlib.sha1(url.encode('utf-8')).hexdigest()[:10]}"


def _domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _meta(**values: Any) -> dict[str, str]:
    return {k: str(v)[:300] for k, v in values.items() if v not in (None, "", [], {})}


def project_queries(project: NormalizedProject) -> dict[str, str]:
    """What to search for a catalog project, per engine."""
    focus = project.interests[0] if project.interests else ""
    return {
        "youtube": clean_query(f"{project.name} project tutorial"),
        "google": clean_query(f"how to build {project.name} guide"),
        "google_scholar": clean_query(f"{project.name} {focus}"),
    }


def resources_from(
    engine: str,
    payload: dict,
    *,
    id_prefix: str,
    tags: tuple[str, ...] = (),
    limit: int = 5,
) -> list[Resource]:
    """SerpApi results -> Resource records. Items without a usable URL are skipped."""
    found: list[Resource] = []
    seen: set[str] = set()

    def add(**fields: Any) -> None:
        url = fields.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            return
        if url in seen or len(found) >= limit:
            return
        seen.add(url)
        title = " ".join(str(fields.pop("title") or "").split())[:300] or url[:300]
        found.append(
            Resource(
                id=f"{id_prefix}/{_slug(engine, url)}",
                title=title,
                topic_tags=tags,
                source=f"serpapi:{engine}",
                **fields,
            )
        )

    if engine == "youtube":
        for v in payload.get("video_results", []) or []:
            add(
                title=v.get("title"),
                url=v.get("link"),
                kind="tutorial",
                provider="YouTube",
                thumbnail_url=(v.get("thumbnail") or {}).get("static"),
                content_excerpt=(v.get("description") or None),
                metadata=_meta(
                    channel=(v.get("channel") or {}).get("name"),
                    published=v.get("published_date"),
                    length=v.get("length"),
                    views=v.get("views"),
                ),
            )
    elif engine == "google_scholar":
        for r in payload.get("organic_results", []) or []:
            info = r.get("publication_info") or {}
            cited = ((r.get("inline_links") or {}).get("cited_by") or {}).get("total")
            add(
                title=r.get("title"),
                url=r.get("link"),
                kind="research",
                provider="Google Scholar",
                content_excerpt=r.get("snippet") or None,
                metadata=_meta(summary=info.get("summary"), cited_by=cited),
            )
    elif engine == "google":
        for r in payload.get("organic_results", []) or []:
            url = r.get("link")
            add(
                title=r.get("title"),
                url=url,
                kind="documentation",
                provider=r.get("source") or (_domain(url) if isinstance(url, str) else None),
                content_excerpt=r.get("snippet") or None,
                metadata=_meta(displayed_link=r.get("displayed_link")),
            )
    else:
        raise ValueError(f"no resource conversion for engine {engine!r}")
    return found


def offers_from(payload: dict, *, limit: int = 3) -> list[dict]:
    """Google Shopping results -> [{title, url, price_usd, source, thumbnail_url}]."""
    offers: list[dict] = []
    for item in payload.get("shopping_results", []) or []:
        url = item.get("product_link") or item.get("link")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            continue
        price = item.get("extracted_price")
        offers.append(
            {
                "title": " ".join(str(item.get("title") or "").split())[:300],
                "url": url,
                "price_usd": float(price) if isinstance(price, int | float) else None,
                "source": (item.get("source") or _domain(url))[:200],
                "thumbnail_url": item.get("thumbnail"),
            }
        )
        if len(offers) >= limit:
            break
    return offers

"""The Caterpillar: conversational mentoring for one catalog project or for a student's own
idea, plus turning a developed idea into a full project starter.

Stateless: the browser sends the whole conversation each turn. The model may link only to
supplied sources (the project's resources, catalog matches, or live web results); any other URL
in its reply is removed before the student sees it.
"""

import re

from ..api.schemas import AssistantRequest, ElaborateIdeaRequest, Notice, StarterRequest
from ..contracts import NormalizedProject, NormalizedUser, Resource
from ..dependencies import AppContext
from ..errors import not_found
from ..llm.prompting import block, load_prompt
from ..search import SearchError, clean_query, resources_from, short_query
from . import generation
from .resources import build_resource_bank

URL_RE = re.compile(r"https?://[^\s<>()\[\]\"']+")
DIG_ENGINES = ("youtube", "google")
STARTER_ENGINES = ("youtube", "google_scholar")
WEB_RESULTS_PER_ENGINE = 3
GENERAL_BANK_SIZE = 8
REMOVED_LINK = "[link removed: not among the supplied sources]"


def _load_user(ctx: AppContext, user_id: str) -> NormalizedUser:
    user = ctx.data.get_user(user_id)
    if user is None:
        raise not_found("user", user_id)
    return user


def _sources_payload(resources: list[Resource]) -> list[dict]:
    return [
        {
            "id": r.id,
            "title": r.title,
            "kind": r.kind,
            "url": r.url,
            "provider": r.provider,
            "excerpt": (r.content_excerpt or "")[:400] or None,
        }
        for r in resources
    ]


def web_search(
    ctx: AppContext, queries: dict[str, str], *, tags: tuple[str, ...]
) -> tuple[list[Resource], list[Notice]]:
    """Live SerpApi results as Resource records, one query per engine. A failing engine does
    not stop the others; every failure is reported in a notice."""
    if not ctx.search.enabled:
        return [], [
            Notice(
                code="SEARCH_UNAVAILABLE",
                message="Web search is not configured on this server (SERPAPI_API_KEY); "
                "answering from supplied sources only.",
            )
        ]
    results: list[Resource] = []
    failures: list[str] = []
    for engine, query in queries.items():
        try:
            payload = ctx.search.search(engine, query)
        except SearchError as exc:
            failures.append(f"{engine}: {exc.message}")
            continue
        results += resources_from(
            engine, payload, id_prefix="web", tags=tags, limit=WEB_RESULTS_PER_ENGINE
        )
    notices = []
    if failures:
        notices.append(
            Notice(code="SEARCH_FAILED", message="Web search failed for " + "; ".join(failures))
        )
    return results, notices


def dig_queries(project: NormalizedProject | None, message: str) -> dict[str, str]:
    """YouTube gets a short query (it returns nothing for long sentences); Google the full one."""
    topic = f"{project.name} " if project else ""
    return {
        "youtube": short_query(f"{topic}{short_query(message, 6)}", 12),
        "google": clean_query(f"{topic}{message}"),
    }


def starter_queries(idea: str) -> dict[str, str]:
    return {
        "youtube": short_query(f"{short_query(idea, 7)} tutorial", 9),
        "google_scholar": clean_query(idea[:150]),
    }


def strip_unknown_urls(text: str, allowed: set[str]) -> tuple[str, int]:
    """Replace every URL that is not in allowed. Returns (text, number removed)."""
    removed = 0

    def replace(match: re.Match) -> str:
        nonlocal removed
        raw = match.group(0)
        url = raw.rstrip(".,;:!?")
        if url in allowed:
            return raw
        removed += 1
        return REMOVED_LINK + raw[len(url) :]

    return URL_RE.sub(replace, text), removed


def _system_prompt(
    user: NormalizedUser,
    project: NormalizedProject | None,
    preferences,
    sources: list[Resource],
    web: list[Resource],
) -> str:
    parts = [load_prompt("assistant_project.md" if project else "assistant_general.md").strip()]
    parts.append(block("student_profile", user.model_dump(mode="json")))
    prefs = preferences.model_dump(mode="json") if preferences else {}
    parts.append(block("preferences", prefs or "none given"))
    if project is not None:
        catalog = project.model_dump(mode="json", exclude={"resources"})
        catalog["resource_ids"] = [r.id for r in project.resources]
        parts.append(block("catalog_project", catalog))
    parts.append(block("sources", _sources_payload(sources)))
    parts.append(
        block(
            "web_results",
            _sources_payload(web) if web else "none (no web search was run for this turn)",
        )
    )
    return "\n\n".join(parts)


def reply(ctx: AppContext, user_id: str, req: AssistantRequest) -> dict:
    user = _load_user(ctx, user_id)
    project = None
    if req.project_id is not None:
        project = ctx.data.get_project(req.project_id)
        if project is None:
            raise not_found("project", req.project_id)

    last_user = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
    if project is not None:
        sources = list(project.resources)
        tags = project.interests[:3]
    else:
        projects = ctx.data.list_projects()
        sources = build_resource_bank(
            projects, [last_user, *user.interests], max_items=GENERAL_BANK_SIZE
        )
        tags = user.interests[:3]

    web: list[Resource] = []
    notices: list[Notice] = []
    if req.dig_deeper:
        web, notices = web_search(ctx, dig_queries(project, last_user), tags=tags)

    llm = ctx.llm
    system = _system_prompt(user, project, req.preferences, sources, web)
    text = llm.chat(system, [(m.role, m.content) for m in req.messages])

    supplied = [*sources, *web]
    text, removed = strip_unknown_urls(text, {r.url for r in supplied if r.url})
    if removed:
        notices.append(
            Notice(
                code="LINKS_REMOVED",
                message=f"{removed} link(s) that were not among the supplied sources were removed.",
            )
        )
    if llm.mode == "mock":
        notices.insert(
            0,
            Notice(
                code="MOCK_GENERATION",
                message="Generated by the offline mock provider, not a real model.",
            ),
        )
    cited = [r for r in supplied if r.url and r.url in text]
    return {
        "mode": "project" if project else "general",
        "user_id": user.id,
        "project_id": project.id if project else None,
        "reply": text,
        "cited_sources": cited,
        "web_results": web,
        "generation_mode": llm.mode,
        "model": getattr(llm, "last_model", llm.model_id),  # the model that actually answered
        "data_source": ctx.data_source,
        "persisted": False,
        "warnings": notices,
    }


def starter(ctx: AppContext, user_id: str, req: StarterRequest) -> dict:
    """A full ProjectPlan for the student's idea, with web sources found for the idea first in
    the resource bank so the plan can point at real tutorials and papers."""
    user = _load_user(ctx, user_id)
    idea_text = req.idea
    if req.conversation:
        notes = "\n".join(
            f"- {m.role}: {' '.join(m.content.split())[:300]}" for m in req.conversation[-8:]
        )
        idea_text = f"{req.idea}\n\nNotes from the mentoring conversation:\n{notes}"
    idea_text = idea_text[:2000].strip()

    web: list[Resource] = []
    notices: list[Notice] = []
    if req.dig_deeper:
        web, notices = web_search(ctx, starter_queries(req.idea), tags=user.interests[:3])
    request = ElaborateIdeaRequest(
        mode="elaborate_idea", idea=idea_text, preferences=req.preferences
    )
    body = generation.elaborate_idea(ctx, user.id, request, extra_resources=web)
    body["mode"] = "starter"
    body["web_results"] = [r.model_dump(mode="json") for r in web]
    body["warnings"] = [n.model_dump() for n in notices] + body["warnings"]
    return body

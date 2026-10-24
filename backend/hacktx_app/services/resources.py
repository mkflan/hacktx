"""In-memory resource bank: supplied resources relevant to the current idea or project."""

from collections.abc import Iterable

from ..contracts import NormalizedProject, Resource
from .normalize import tokens

MAX_BANK_SIZE = 12


def _resource_tokens(resource: Resource, parent: NormalizedProject) -> frozenset[str]:
    words: set[str] = set(tokens(resource.title))
    for tag in (*resource.topic_tags, *parent.interests, parent.name):
        words |= tokens(tag)
    return frozenset(words)


def build_resource_bank(
    projects: Iterable[NormalizedProject],
    focus_texts: Iterable[str],
    primary: NormalizedProject | None = None,
    max_items: int = MAX_BANK_SIZE,
) -> list[Resource]:
    """Primary project's resources first, then others ranked by token overlap with the focus."""
    focus: set[str] = set()
    for text in focus_texts:
        if text:
            focus |= tokens(text)

    bank: dict[str, Resource] = {}
    if primary is not None:
        for resource in primary.resources:
            bank.setdefault(resource.id, resource)

    scored: list[tuple[int, str, Resource]] = []
    for project in projects:
        for resource in project.resources:
            if resource.id in bank:
                continue
            overlap = len(_resource_tokens(resource, project) & focus)
            if overlap:
                scored.append((overlap, resource.id, resource))
    scored.sort(key=lambda item: (-item[0], item[1]))
    for _, resource_id, resource in scored:
        if len(bank) >= max_items:
            break
        bank.setdefault(resource_id, resource)
    return list(bank.values())[:max_items]


def hydrate(ids: Iterable[str], bank: list[Resource]) -> list[Resource]:
    by_id = {r.id: r for r in bank}
    result: list[Resource] = []
    seen: set[str] = set()
    for resource_id in ids:
        if resource_id in by_id and resource_id not in seen:
            seen.add(resource_id)
            result.append(by_id[resource_id])
    return result


def default_search_queries(focus: str, interests: Iterable[str]) -> list[str]:
    """Search suggestions for when no supplied resource fits. Labeled as suggestions."""
    focus = " ".join(focus.split()[:12])
    queries = [f"{focus} beginner tutorial", f"{focus} research overview"]
    queries += [f"{focus} {interest} example project" for interest in list(interests)[:2]]
    return queries

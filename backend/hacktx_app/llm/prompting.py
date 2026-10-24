"""Prompt files and the user message built from selected context."""

import hashlib
import json
from functools import cache
from pathlib import Path

from ..api.schemas import PersonalizationPreferences
from ..contracts import NormalizedProject, NormalizedUser, Resource

PROMPTS_DIR = Path(__file__).parent / "prompts"
PROMPT_FILES = ("system.md", "generate_ideas.md", "elaborate_idea.md", "personalize_project.md")
EXCERPT_CHARS = 600


@cache
def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


@cache
def prompt_version() -> str:
    digest = hashlib.sha256()
    for name in PROMPT_FILES:
        digest.update(load_prompt(name).encode("utf-8"))
    return digest.hexdigest()[:12]


def _block(tag: str, payload: object) -> str:
    return f"<{tag}>\n{json.dumps(payload, ensure_ascii=False, indent=1)}\n</{tag}>"


def bank_payload(bank: list[Resource]) -> list[dict]:
    return [
        {
            "id": r.id,
            "title": r.title,
            "kind": r.kind,
            "url": r.url,
            "provider": r.provider,
            "topic_tags": list(r.topic_tags),
            "content_excerpt": (r.content_excerpt or "")[:EXCERPT_CHARS] or None,
        }
        for r in bank
    ]


def build_user_message(
    task: str,
    user: NormalizedUser,
    preferences: PersonalizationPreferences | None,
    resource_bank: list[Resource],
    *,
    idea: str | None = None,
    project: NormalizedProject | None = None,
) -> str:
    parts = [task.strip()]
    parts.append(_block("student_profile", user.model_dump(mode="json")))
    prefs = preferences.model_dump(mode="json") if preferences else {}
    parts.append(_block("preferences", prefs or "none given"))
    if idea is not None:
        parts.append(f"<student_idea>\n{idea}\n</student_idea>")
    if project is not None:
        catalog = project.model_dump(mode="json", exclude={"resources"})
        catalog["resource_ids"] = [r.id for r in project.resources]
        parts.append(_block("catalog_project", catalog))
    parts.append(_block("resource_bank", bank_payload(resource_bank)))
    return "\n\n".join(parts)

"""Text normalization for matching. Original strings are kept elsewhere for display."""

import re
from collections.abc import Iterable

_SEPARATORS = re.compile(r"[-_/,&+]+")
_NON_WORD = re.compile(r"[^\w\s]")
_SPACES = re.compile(r"\s+")

MAJOR_ALIASES = {
    "ece": "electrical and computer engineering",
    "ee": "electrical engineering",
    "electrical computer engineering": "electrical and computer engineering",
    "cs": "computer science",
    "comp sci": "computer science",
    "compsci": "computer science",
    "me": "mechanical engineering",
    "mech e": "mechanical engineering",
    "mechanical": "mechanical engineering",
}

# Words too broad to count as an interest match by themselves ("machine learning" is not
# "language learning", "data science" is not "data visualization").
GENERIC_TOKENS = frozenset(
    {
        "a", "an", "and", "the", "of", "for", "in", "on", "to", "with", "or",
        "data", "learning", "system", "design", "engineering", "science", "project", "tool",
    }
)  # fmt: skip


def norm_text(value: str) -> str:
    value = _SEPARATORS.sub(" ", value.casefold())
    value = _NON_WORD.sub("", value)
    return _SPACES.sub(" ", value).strip()


def norm_major(value: str) -> str:
    text = norm_text(value)
    return MAJOR_ALIASES.get(text, text)


def _singular(token: str) -> str:
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokens(value: str) -> frozenset[str]:
    """Meaningful word tokens (singularized, generic words removed)."""
    return frozenset(
        _singular(t) for t in norm_text(value).split() if _singular(t) not in GENERIC_TOKENS
    )


def unique_tags(values: Iterable[str]) -> list[str]:
    """Deduplicate by normalized form, keeping the first original spelling."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = norm_text(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value.strip())
    return result


def tags_match(a: str, b: str) -> bool:
    """Same normalized tag, or at least one shared meaningful token."""
    if norm_text(a) == norm_text(b):
        return True
    return bool(tokens(a) & tokens(b))


def matched_interests(user_interests: Iterable[str], item_tags: Iterable[str]) -> list[str]:
    """User interests (original spelling) that match any of the item's tags."""
    item_tags = list(item_tags)
    return [i for i in unique_tags(user_interests) if any(tags_match(i, t) for t in item_tags)]


def majors_match(user_major: str, project_majors: Iterable[str]) -> list[str]:
    """Project majors (original spelling) equal to the user's major after alias handling."""
    target = norm_major(user_major)
    if not target:
        return []
    return [m for m in project_majors if norm_major(m) == target]

"""Explore tab: filter, paginate and group the shared catalog. No user and no LLM involved."""

from collections import Counter

from ..api.schemas import Notice, ProjectCard, ProjectGroup, ProjectsQuery, missing_fields
from ..contracts import NormalizedProject
from .normalize import majors_match, norm_major, norm_text, tags_match

UNSPECIFIED_KEY = "unspecified"


def project_sort_key(project: NormalizedProject) -> tuple[str, str]:
    return (project.id.casefold(), project.id)


def unique_projects(projects: list[NormalizedProject]) -> tuple[list[NormalizedProject], list]:
    """Drop duplicate IDs (first wins) and return them in stable ID order."""
    seen: dict[str, NormalizedProject] = {}
    notices: list[Notice] = []
    for project in projects:
        if project.id in seen:
            notices.append(
                Notice(
                    code="DUPLICATE_PROJECT_ID",
                    message="The data provider returned a duplicate project ID; kept the first.",
                    project_id=project.id,
                )
            )
            continue
        seen[project.id] = project
    return sorted(seen.values(), key=project_sort_key), notices


def _matches(project: NormalizedProject, query: ProjectsQuery) -> bool:
    if query.major and not majors_match(query.major, project.associated_majors):
        return False
    if query.interest and not any(tags_match(query.interest, t) for t in project.interests):
        return False
    if query.difficulty and project.difficulty != query.difficulty:
        return False
    return True


def _group(page: list[NormalizedProject], group_by: str) -> list[ProjectGroup]:
    groups: dict[str, ProjectGroup] = {}
    for project in page:
        tags = project.associated_majors if group_by == "major" else project.interests
        normalize = norm_major if group_by == "major" else norm_text
        keys: dict[str, str] = {}
        for tag in tags:
            keys.setdefault(normalize(tag), tag)
        if not keys:
            keys = {UNSPECIFIED_KEY: "Unspecified"}
        card = ProjectCard.from_project(project)
        for key, label in keys.items():
            group = groups.setdefault(key, ProjectGroup(key=key, label=label, projects=[]))
            group.projects.append(card)
    return sorted(groups.values(), key=lambda g: (g.key == UNSPECIFIED_KEY, g.label.casefold()))


def list_catalog(projects: list[NormalizedProject], query: ProjectsQuery) -> dict:
    ordered, notices = unique_projects(projects)
    matching = [p for p in ordered if _matches(p, query)]
    page = matching[query.offset : query.offset + query.limit]

    if query.difficulty:
        unknown = sum(1 for p in ordered if p.difficulty is None and _matches_ignoring(p, query))
        if unknown:
            notices.append(
                Notice(
                    code="UNKNOWN_DIFFICULTY_EXCLUDED",
                    message=(
                        f"{unknown} project(s) with unknown difficulty were left out because a "
                        "difficulty filter was applied."
                    ),
                )
            )
    if not matching:
        notices.append(Notice(code="NO_MATCHES", message="No projects match these filters."))

    return {
        "groups": _group(page, query.group_by),
        "total": len(matching),
        "limit": query.limit,
        "offset": query.offset,
        "warnings": notices,
    }


def _matches_ignoring(project: NormalizedProject, query: ProjectsQuery) -> bool:
    return _matches(project, query.model_copy(update={"difficulty": None}))


def facets(projects: list[NormalizedProject]) -> dict:
    ordered, notices = unique_projects(projects)
    majors: dict[str, str] = {}
    major_counts: Counter[str] = Counter()
    interests: dict[str, str] = {}
    interest_counts: Counter[str] = Counter()
    difficulty_counts: Counter[str] = Counter()
    for project in ordered:
        for key, label in {norm_major(m): m for m in project.associated_majors}.items():
            majors.setdefault(key, label)
            major_counts[key] += 1
        for key, label in {norm_text(i): i for i in project.interests}.items():
            interests.setdefault(key, label)
            interest_counts[key] += 1
        difficulty_counts[project.difficulty or "unknown"] += 1

    def options(labels: dict[str, str], counts: Counter[str]) -> list[dict]:
        return [
            {"key": k, "label": labels[k], "count": counts[k]}
            for k in sorted(labels, key=lambda k: labels[k].casefold())
        ]

    order = ["beginner", "intermediate", "advanced", "unknown"]
    return {
        "majors": options(majors, major_counts),
        "interests": options(interests, interest_counts),
        "difficulties": [
            {"key": d, "label": d.capitalize(), "count": difficulty_counts[d]}
            for d in order
            if difficulty_counts[d]
        ],
        "warnings": notices,
    }


def project_details(project: NormalizedProject) -> dict:
    missing = missing_fields(project)
    notices = []
    if "resources" in missing:
        notices.append(
            Notice(
                code="NO_RESOURCES",
                message="No guides, tutorials or research were supplied for this project.",
                project_id=project.id,
            )
        )
    if any(r.verification_status == "provided_unverified" for r in project.resources):
        notices.append(
            Notice(
                code="RESOURCES_UNVERIFIED",
                message="Supplied resource links have not been verified.",
                project_id=project.id,
            )
        )
    return {"project": project, "missing_details": missing, "warnings": notices}

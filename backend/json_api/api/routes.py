"""HTTP routes. Thin: validate input, call a service, return JSON."""

from collections.abc import Iterator
from contextlib import contextmanager

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, TypeAdapter, ValidationError

from ..dependencies import get_context
from ..errors import not_found, request_validation
from ..services import assistant, catalog, generation, ranking
from .schemas import (
    AssistantRequest,
    PathId,
    PersonalizeRequest,
    ProjectsQuery,
    RecommendationsRequest,
    StarterRequest,
    UserSummary,
    chat_request_adapter,
)

bp = Blueprint("hacktx_api", __name__)
_path_id = TypeAdapter(PathId)


def _json(payload: dict | BaseModel, status: int = 200):
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json")
    return jsonify(_dump(payload)), status


def _dump(value):
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {k: _dump(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_dump(v) for v in value]
    return value


@contextmanager
def _bad_request() -> Iterator[None]:
    """Only validation of what the caller sent becomes a 422; anything else is a server error."""
    try:
        yield
    except ValidationError as exc:
        raise request_validation(exc) from exc


def _body[M: BaseModel](model: type[M]) -> M:
    raw = request.get_data(cache=False) or b"{}"
    with _bad_request():
        return model.model_validate_json(raw)


def _id(value: str) -> str:
    with _bad_request():
        return _path_id.validate_python(value)


@bp.get("/health")
def health():
    ctx = get_context()
    llm = ctx.llm_provider
    return _json(
        {
            "status": "ok",
            "data_mode": ctx.settings.data_mode,
            "data_source": ctx.data_source,
            "data_provider_configured": ctx.data_provider is not None,
            "llm_mode": ctx.settings.llm_mode,
            "llm_configured": llm is not None,
            "llm_model": llm.model_id if llm else None,
            "search_enabled": ctx.search.enabled,
            "persistence": "none (generated plans are not saved)",
        }
    )


@bp.get("/api/users")
def list_users():
    ctx = get_context()
    users = [
        UserSummary(id=u.id, username=u.username, major=u.major) for u in ctx.data.list_users()
    ]
    return _json({"users": users, "data_source": ctx.data_source})


@bp.get("/api/users/<user_id>")
def get_user(user_id: str):
    ctx = get_context()
    user = ctx.data.get_user(_id(user_id))
    if user is None:
        raise not_found("user", user_id)
    return _json({"user": user, "data_source": ctx.data_source})


# Static project routes are registered before the dynamic /<project_id> route.
@bp.get("/api/projects")
def list_projects():
    ctx = get_context()
    with _bad_request():
        query = ProjectsQuery.model_validate(request.args.to_dict())
    result = catalog.list_catalog(ctx.data.list_projects(), query)
    return _json({**result, "data_source": ctx.data_source})


@bp.get("/api/projects/facets")
def project_facets():
    ctx = get_context()
    return _json({**catalog.facets(ctx.data.list_projects()), "data_source": ctx.data_source})


@bp.get("/api/projects/<project_id>")
def get_project(project_id: str):
    ctx = get_context()
    project = ctx.data.get_project(_id(project_id))
    if project is None:
        raise not_found("project", project_id)
    return _json({**catalog.project_details(project), "data_source": ctx.data_source})


@bp.post("/api/users/<user_id>/recommendations")
def recommendations(user_id: str):
    """Read-only computation; POST only because it takes a JSON body."""
    ctx = get_context()
    body = _body(RecommendationsRequest)
    user = ctx.data.get_user(_id(user_id))
    if user is None:
        raise not_found("user", user_id)
    cards, warnings = ranking.recommend(
        user, ctx.data.list_projects(), body.preferences, body.limit
    )
    return _json(
        {
            "user_id": user.id,
            "projects": cards,
            "data_source": ctx.data_source,
            "warnings": warnings,
        }
    )


@bp.post("/api/users/<user_id>/chat")
def chat(user_id: str):
    ctx = get_context()
    with _bad_request():
        body = chat_request_adapter.validate_json(request.get_data(cache=False) or b"{}")
    if body.mode == "generate_ideas":
        return _json(generation.generate_ideas(ctx, _id(user_id), body))
    return _json(generation.elaborate_idea(ctx, _id(user_id), body))


@bp.post("/api/users/<user_id>/projects/<project_id>/personalize")
def personalize(user_id: str, project_id: str):
    ctx = get_context()
    body = _body(PersonalizeRequest)
    return _json(generation.personalize_project(ctx, _id(user_id), _id(project_id), body))


@bp.post("/api/users/<user_id>/assistant")
def assistant_reply(user_id: str):
    """One turn with the Caterpillar (project mode when project_id is given)."""
    ctx = get_context()
    body = _body(AssistantRequest)
    return _json(assistant.reply(ctx, _id(user_id), body))


@bp.post("/api/users/<user_id>/starter")
def assistant_starter(user_id: str):
    """Turn a developed idea into a full project starter with web sources."""
    ctx = get_context()
    body = _body(StarterRequest)
    return _json(assistant.starter(ctx, _id(user_id), body))

"""App factory and registration seam.

Standalone:     create_app(data_provider=..., llm_provider=...)
Teammate's app: init_app(existing_flask_app, data_provider=TheirProvider())
"""

import logging

from flask import Flask, request

from .config import Settings
from .contracts import ProjectDataProvider
from .dependencies import EXTENSION_KEY, AppContext
from .errors import register_error_handlers
from .llm.base import LLMProvider
from .services.cache import TTLCache

logger = logging.getLogger("hacktx_app")


def _resolve_data(
    settings: Settings, data_provider: ProjectDataProvider | None
) -> tuple[ProjectDataProvider | None, str]:
    if data_provider is not None:
        return data_provider, getattr(data_provider, "data_source", "injected")
    if settings.data_mode == "fake":
        from .dev.fake_provider import InMemoryProjectDataProvider

        return InMemoryProjectDataProvider(), "fake"
    # DATA_MODE=injected without a provider: report it, never fall back to fake data.
    return None, "injected"


def _resolve_llm(
    settings: Settings, llm_provider: LLMProvider | None
) -> tuple[LLMProvider | None, str | None]:
    if llm_provider is not None:
        return llm_provider, None
    if settings.llm_mode == "mock":
        from .llm.mock import MockLLMProvider

        return MockLLMProvider(), None
    from .llm.anthropic_provider import AnthropicLLMProvider, LLMNotConfiguredError

    try:
        return AnthropicLLMProvider(settings), None
    except LLMNotConfiguredError:
        return None, "LLM_MODE=anthropic but ANTHROPIC_API_KEY is not set on the server."


def init_app(
    app: Flask,
    *,
    data_provider: ProjectDataProvider | None = None,
    llm_provider: LLMProvider | None = None,
    settings: Settings | None = None,
) -> Flask:
    """Register routes, error handlers and CORS on an existing Flask app."""
    from .api.routes import bp

    settings = settings or Settings.from_env()
    data, data_source = _resolve_data(settings, data_provider)
    llm, llm_reason = _resolve_llm(settings, llm_provider)
    app.extensions[EXTENSION_KEY] = AppContext(
        settings=settings,
        data_provider=data,
        data_source=data_source,
        llm_provider=llm,
        llm_unavailable_reason=llm_reason,
        cache=TTLCache(settings.cache_max_entries, settings.cache_ttl_seconds),
    )
    # Flask ships MAX_CONTENT_LENGTH=None, so setdefault would never apply our bound.
    if app.config.get("MAX_CONTENT_LENGTH") is None:
        app.config["MAX_CONTENT_LENGTH"] = settings.max_request_bytes
    app.json.sort_keys = False
    app.register_blueprint(bp)
    register_error_handlers(app)

    allowed = frozenset(settings.cors_origins)

    @app.after_request
    def _cors(response):
        origin = request.headers.get("Origin")
        if origin and origin in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.vary.add("Origin")
        return response

    if data is None:
        logger.warning("DATA_MODE=injected and no data provider registered; data routes return 503")
    if llm is None:
        logger.warning("LLM provider not configured: %s", llm_reason)
    return app


def create_app(
    data_provider: ProjectDataProvider | None = None,
    llm_provider: LLMProvider | None = None,
    settings: Settings | None = None,
) -> Flask:
    app = Flask(__name__)
    return init_app(app, data_provider=data_provider, llm_provider=llm_provider, settings=settings)

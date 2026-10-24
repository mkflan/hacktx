"""The single injection seam. Routes and services get providers only through here."""

import logging
from dataclasses import dataclass
from typing import Any

from flask import current_app

from .config import Settings
from .contracts import NormalizedProject, NormalizedUser, ProjectDataProvider
from .errors import AppError
from .llm.base import LLMProvider
from .services.cache import TTLCache

logger = logging.getLogger("hacktx_app")
EXTENSION_KEY = "hacktx_app"


class SafeDataProvider:
    """Wraps the injected provider: checks returned shapes and turns unexpected failures into
    503 DATA_UNAVAILABLE so a broken database never looks like an empty catalog."""

    def __init__(self, inner: ProjectDataProvider) -> None:
        self._inner = inner

    def _call(self, name: str, *args: Any) -> Any:
        try:
            return getattr(self._inner, name)(*args)
        except AppError:
            raise
        except Exception as exc:
            logger.exception("Data provider %s failed", name)
            raise AppError(
                "DATA_UNAVAILABLE", "Project data is temporarily unavailable.", 503, retryable=True
            ) from exc

    @staticmethod
    def _coerce(model: type, value: Any) -> Any:
        if isinstance(value, model):
            return value
        try:
            return model.model_validate(value)
        except Exception as exc:
            logger.error("Data provider returned a %s that breaks the contract", model.__name__)
            raise AppError(
                "DATA_CONTRACT_ERROR",
                "Project data did not match the application contract.",
                503,
            ) from exc

    def list_users(self) -> list[NormalizedUser]:
        return [self._coerce(NormalizedUser, u) for u in self._call("list_users")]

    def get_user(self, user_id: str) -> NormalizedUser | None:
        user = self._call("get_user", user_id)
        return None if user is None else self._coerce(NormalizedUser, user)

    def list_projects(self) -> list[NormalizedProject]:
        return [self._coerce(NormalizedProject, p) for p in self._call("list_projects")]

    def get_project(self, project_id: str) -> NormalizedProject | None:
        project = self._call("get_project", project_id)
        return None if project is None else self._coerce(NormalizedProject, project)


@dataclass
class AppContext:
    settings: Settings
    data_provider: ProjectDataProvider | None
    data_source: str
    llm_provider: LLMProvider | None
    llm_unavailable_reason: str | None
    cache: TTLCache

    @property
    def data(self) -> SafeDataProvider:
        if self.data_provider is None:
            raise AppError(
                "DATA_PROVIDER_NOT_CONFIGURED",
                "DATA_MODE=injected but no data provider was registered with init_app().",
                503,
            )
        return SafeDataProvider(self.data_provider)

    @property
    def llm(self) -> LLMProvider:
        if self.llm_provider is None:
            raise AppError(
                "LLM_NOT_CONFIGURED",
                self.llm_unavailable_reason or "No LLM provider is configured.",
                503,
            )
        return self.llm_provider


def get_context() -> AppContext:
    return current_app.extensions[EXTENSION_KEY]


def get_data_provider() -> SafeDataProvider:
    return get_context().data


def get_llm_provider() -> LLMProvider:
    return get_context().llm

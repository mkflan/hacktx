"""Real provider: one structured-output Claude call per action, at most one correction.

Retries are coordinated here, not in the SDK (max_retries=0), and every call shares one total
deadline. No silent fallback to mock: failures become 503 (unavailable) or 502 (bad output).
"""

import json
import logging
import time
from collections.abc import Callable
from typing import Any

import anthropic
from pydantic import BaseModel

from ..api.schemas import PersonalizationPreferences
from ..config import Settings
from ..contracts import NormalizedProject, NormalizedUser, Resource
from ..errors import AppError
from .prompting import build_user_message, load_prompt
from .schemas import IdeasDraft, ProjectPlanDraft
from .validation import parse_draft, validate_ideas, validate_plan

logger = logging.getLogger("hacktx_app")

FALLBACK_BETA = "server-side-fallback-2026-07-01"
MIN_SECONDS_FOR_CORRECTION = 8.0
_UNSUPPORTED_SCHEMA_KEYS = frozenset(
    {
        "title", "default", "minLength", "maxLength", "minimum", "maximum",
        "exclusiveMinimum", "exclusiveMaximum", "minItems", "maxItems", "pattern", "format",
    }
)  # fmt: skip


class LLMNotConfiguredError(Exception):
    """Raised at startup when LLM_MODE=anthropic but no API key is set."""


def strict_json_schema(model: type[BaseModel]) -> dict:
    """Pydantic schema -> structured-output schema: closed objects, every property required,
    numeric/length bounds removed (they are enforced by our own validation afterwards)."""

    def clean(node: Any) -> Any:
        if isinstance(node, dict):
            out: dict = {}
            for key, value in node.items():
                if key in _UNSUPPORTED_SCHEMA_KEYS:
                    continue
                if key in ("properties", "$defs"):
                    # Keys here are field and model names, not schema keywords: a field called
                    # "title" must survive even though the "title" keyword is stripped.
                    out[key] = {name: clean(sub) for name, sub in value.items()}
                else:
                    out[key] = clean(value)
            if out.get("type") == "object" and "properties" in out:
                out["additionalProperties"] = False
                out["required"] = list(out["properties"])
            return out
        if isinstance(node, list):
            return [clean(item) for item in node]
        return node

    return clean(model.model_json_schema())


class AnthropicLLMProvider:
    mode = "anthropic"

    def __init__(self, settings: Settings, client: Any = None) -> None:
        if client is None:
            if not settings.anthropic_api_key:
                raise LLMNotConfiguredError("ANTHROPIC_API_KEY is not set")
            client = anthropic.Anthropic(
                api_key=settings.anthropic_api_key,
                max_retries=0,
                timeout=settings.llm_deadline_seconds,
            )
        self._client = client
        self._settings = settings
        self.model_id = settings.anthropic_model

    # ---- public actions ---------------------------------------------------------------------

    def generate_ideas(
        self,
        user: NormalizedUser,
        preferences: PersonalizationPreferences | None,
        topic: str | None,
        resource_bank: list[Resource],
        limit: int = 3,
    ) -> IdeasDraft:
        topic_line = f"Focus topic from the student: {topic}" if topic else "No topic was given."
        task = load_prompt("generate_ideas.md").format(limit=limit, topic_line=topic_line)
        message = build_user_message(task, user, preferences, resource_bank)
        return self._run(IdeasDraft, message, validate_ideas)

    def elaborate_idea(
        self,
        user: NormalizedUser,
        preferences: PersonalizationPreferences | None,
        idea: str,
        resource_bank: list[Resource],
    ) -> ProjectPlanDraft:
        task = load_prompt("elaborate_idea.md")
        message = build_user_message(task, user, preferences, resource_bank, idea=idea)
        return self._run(ProjectPlanDraft, message, lambda d: validate_plan(d, resource_bank, user))

    def personalize_project(
        self,
        user: NormalizedUser,
        preferences: PersonalizationPreferences | None,
        project: NormalizedProject,
        resource_bank: list[Resource],
    ) -> ProjectPlanDraft:
        task = load_prompt("personalize_project.md")
        message = build_user_message(task, user, preferences, resource_bank, project=project)
        return self._run(ProjectPlanDraft, message, lambda d: validate_plan(d, resource_bank, user))

    # ---- call + one correction --------------------------------------------------------------

    def _run[M: BaseModel](
        self, model: type[M], message: str, check: Callable[[M], list[str]]
    ) -> M:
        deadline = time.monotonic() + self._settings.llm_deadline_seconds
        schema = strict_json_schema(model)

        text, errors = self._attempt(message, schema, deadline)
        draft = None
        if not errors:
            draft, errors = self._parse(model, text, check)
        if not errors:
            return draft

        if deadline - time.monotonic() < MIN_SECONDS_FOR_CORRECTION:
            raise _invalid_output(errors)
        logger.info("LLM output failed validation; requesting one correction: %s", errors[:5])
        correction = (
            f"{message}\n\nA previous attempt returned this output:\n<previous_output>\n"
            f"{(text or '')[:20000]}\n</previous_output>\n\nIt failed these checks:\n"
            + "\n".join(f"- {e}" for e in errors)
            + "\n\nReturn a complete corrected JSON object that passes every check."
        )
        text, errors = self._attempt(correction, schema, deadline)
        if not errors:
            draft, errors = self._parse(model, text, check)
        if errors:
            raise _invalid_output(errors)
        return draft

    @staticmethod
    def _parse[M: BaseModel](
        model: type[M], text: str | None, check: Callable[[M], list[str]]
    ) -> tuple[M | None, list[str]]:
        try:
            data = json.loads(text or "")
        except json.JSONDecodeError:
            return None, ["output was not valid JSON"]
        draft, errors = parse_draft(model, data)
        if draft is None:
            return None, errors
        return draft, check(draft)

    def _attempt(self, message: str, schema: dict, deadline: float) -> tuple[str | None, list[str]]:
        """One API call. Returns (text, errors); raises AppError for non-retryable failures."""
        remaining = deadline - time.monotonic()
        if remaining <= 1:
            raise AppError("LLM_TIMEOUT", "The model did not answer in time.", 503, retryable=True)

        request = {
            "model": self._settings.anthropic_model,
            "max_tokens": self._settings.llm_max_tokens,
            "system": load_prompt("system.md"),
            "messages": [{"role": "user", "content": message}],
            "output_config": {
                "effort": self._settings.anthropic_effort,
                "format": {"type": "json_schema", "schema": schema},
            },
            "timeout": remaining,
        }
        try:
            if self._settings.anthropic_fallbacks:
                response = self._client.beta.messages.create(
                    **request, betas=[FALLBACK_BETA], fallbacks="default"
                )
            else:
                response = self._client.messages.create(**request)
        except anthropic.APITimeoutError as exc:
            raise AppError(
                "LLM_TIMEOUT", "The model did not answer in time.", 503, retryable=True
            ) from exc
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            raise AppError(
                "LLM_AUTH_FAILED", "The model provider rejected the server credentials.", 503
            ) from exc
        except anthropic.RateLimitError as exc:
            raise AppError(
                "LLM_RATE_LIMITED",
                "The model provider is rate limiting; try again shortly.",
                503,
                retryable=True,
            ) from exc
        except anthropic.APIConnectionError as exc:
            raise AppError(
                "LLM_UNAVAILABLE", "Could not reach the model provider.", 503, retryable=True
            ) from exc
        except anthropic.APIStatusError as exc:
            if exc.status_code >= 500:
                raise AppError(
                    "LLM_UNAVAILABLE", "The model provider is unavailable.", 503, retryable=True
                ) from exc
            logger.warning("Model request rejected: status=%s", exc.status_code)
            raise AppError(
                "LLM_REQUEST_REJECTED", "The model provider rejected the request.", 502
            ) from exc

        if response.stop_reason == "refusal":
            raise AppError("LLM_REFUSED", "The model declined this request.", 502)
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        if response.stop_reason == "max_tokens":
            return text, ["output was truncated; return a shorter, complete JSON object"]
        return text, []


def _invalid_output(errors: list[str]) -> AppError:
    return AppError(
        "LLM_INVALID_OUTPUT",
        "The model returned output that failed validation after one correction.",
        502,
        retryable=True,
        details=[{"msg": e} for e in errors[:10]],
    )

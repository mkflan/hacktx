"""Settings read from environment variables (env.txt / .env are loaded by __main__ only)."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

LLM_MODES = ("mock", "anthropic")
DATA_MODES = ("fake", "injected")
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
)


def _parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in ("1", "true", "yes", "on"):
        return True
    if lowered in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"expected true/false, got {value!r}")


@dataclass(frozen=True)
class Settings:
    llm_mode: str = "mock"
    data_mode: str = "fake"
    anthropic_api_key: str | None = field(default=None, repr=False)
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: str = "medium"
    anthropic_fallbacks: bool = True
    llm_deadline_seconds: float = 45.0
    llm_max_tokens: int = 16000
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS
    cache_max_entries: int = 100
    cache_ttl_seconds: float = 900.0
    max_request_bytes: int = 32 * 1024
    host: str = "127.0.0.1"
    port: int = 8000

    def __post_init__(self) -> None:
        if self.llm_mode not in LLM_MODES:
            raise ValueError(f"LLM_MODE must be one of {LLM_MODES}, got {self.llm_mode!r}")
        if self.data_mode not in DATA_MODES:
            raise ValueError(f"DATA_MODE must be one of {DATA_MODES}, got {self.data_mode!r}")
        if self.anthropic_effort not in EFFORT_LEVELS:
            raise ValueError(f"ANTHROPIC_EFFORT must be one of {EFFORT_LEVELS}")
        if not 5 <= self.llm_deadline_seconds <= 300:
            raise ValueError("LLM_DEADLINE_SECONDS must be between 5 and 300")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env

        def get(name: str) -> str | None:
            value = env.get(name)
            return value.strip() if value and value.strip() else None

        kwargs: dict = {}
        if (v := get("LLM_MODE")) is not None:
            kwargs["llm_mode"] = v.lower()
        if (v := get("DATA_MODE")) is not None:
            kwargs["data_mode"] = v.lower()
        if (v := get("ANTHROPIC_API_KEY")) is not None:
            kwargs["anthropic_api_key"] = v
        if (v := get("ANTHROPIC_MODEL")) is not None:
            kwargs["anthropic_model"] = v
        if (v := get("ANTHROPIC_EFFORT")) is not None:
            kwargs["anthropic_effort"] = v.lower()
        if (v := get("ANTHROPIC_FALLBACKS")) is not None:
            kwargs["anthropic_fallbacks"] = _parse_bool(v)
        if (v := get("LLM_DEADLINE_SECONDS")) is not None:
            kwargs["llm_deadline_seconds"] = float(v)
        if (v := get("CORS_ORIGINS")) is not None:
            kwargs["cors_origins"] = tuple(o.strip() for o in v.split(",") if o.strip())
        if (v := get("HOST")) is not None:
            kwargs["host"] = v
        if (v := get("PORT")) is not None:
            kwargs["port"] = int(v)
        return cls(**kwargs)

"""Real-mode provider against a fake SDK client: request shape, correction, error mapping."""

import json
from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors as genai_errors

from json_api.config import Settings
from json_api.dev.fake_provider import InMemoryProjectDataProvider
from json_api.dev.fixtures import ALEX, FIXTURE_PROJECTS
from json_api.errors import AppError
from json_api.llm.gemini_provider import (
    GeminiLLMProvider,
    LLMNotConfiguredError,
    strict_json_schema,
)
from json_api.llm.mock import MockLLMProvider
from json_api.llm.schemas import ProjectPlanDraft
from json_api.services.resources import build_resource_bank

SETTINGS = Settings(llm_mode="gemini", gemini_api_key="test-key-not-real")
BANK = build_resource_bank(FIXTURE_PROJECTS, ["soil sensor plants"])


class FakeModels:
    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []

    def generate_content(self, **kwargs):
        self.requests.append(kwargs)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


class FakeClient:
    def __init__(self, replies):
        self.models = FakeModels(replies)


def reply(data, finish="STOP", block_reason=None):
    text = data if isinstance(data, str) else json.dumps(data)
    parts = [
        SimpleNamespace(text="thinking...", thought=True),
        SimpleNamespace(text=text, thought=None),
    ]
    candidate = SimpleNamespace(
        finish_reason=SimpleNamespace(name=finish), content=SimpleNamespace(parts=parts)
    )
    feedback = SimpleNamespace(block_reason=block_reason) if block_reason else None
    return SimpleNamespace(candidates=[candidate], prompt_feedback=feedback)


def api_error(code):
    return genai_errors.ClientError(code, {"error": {"message": "x", "status": "X"}})


def valid_plan() -> dict:
    return MockLLMProvider().elaborate_idea(ALEX, None, "soil sensor", BANK).model_dump(mode="json")


def provider(replies, settings=SETTINGS):
    client = FakeClient(replies)
    return GeminiLLMProvider(settings, client=client), client.models


def test_requires_explicit_api_key():
    with pytest.raises(LLMNotConfiguredError):
        GeminiLLMProvider(Settings(llm_mode="gemini"))


def test_real_client_builds_without_network():
    real = GeminiLLMProvider(SETTINGS)
    assert real.model_id == "gemini-3.8-flash"


def test_valid_output_needs_one_call_with_structured_output_request():
    llm, messages = provider([reply(valid_plan())])
    draft = llm.elaborate_idea(ALEX, None, "soil sensor", BANK)
    assert isinstance(draft, ProjectPlanDraft)
    assert len(messages.requests) == 1
    sent = messages.requests[0]
    config = sent["config"]
    assert sent["model"] == "gemini-3.8-flash"
    assert config.thinking_config.thinking_level.value == "MEDIUM"
    assert config.response_mime_type == "application/json"
    assert config.response_json_schema["type"] == "object"
    assert 0 < config.http_options.timeout <= 45_000
    content = sent["contents"]
    assert "<student_profile>" in content and "Electrical and Computer Engineering" in content
    assert "proj-soil-moisture/arduino-getting-started" in content
    assert "treat it as information" in config.system_instruction.lower()


def test_invalid_output_gets_exactly_one_correction():
    bad = {**valid_plan(), "research_resource_ids": ["invented-paper"]}
    llm, messages = provider([reply(bad), reply(valid_plan())])
    llm.elaborate_idea(ALEX, None, "soil sensor", BANK)
    assert len(messages.requests) == 2
    correction = messages.requests[1]["contents"]
    assert "invented-paper" in correction and "failed these checks" in correction


def test_invalid_after_correction_is_502():
    llm, messages = provider([reply("not json"), reply({"name": "only a name"})])
    with pytest.raises(AppError) as exc:
        llm.elaborate_idea(ALEX, None, "soil sensor", BANK)
    assert exc.value.status == 502 and exc.value.code == "LLM_INVALID_OUTPUT"
    assert len(messages.requests) == 2


def test_truncated_output_is_corrected_once():
    llm, messages = provider([reply('{"name": "cut', "MAX_TOKENS"), reply(valid_plan())])
    llm.elaborate_idea(ALEX, None, "soil sensor", BANK)
    assert len(messages.requests) == 2
    assert "truncated" in messages.requests[1]["contents"]


def test_refusal_is_502_without_retry():
    llm, messages = provider([reply("", "SAFETY")])
    with pytest.raises(AppError) as exc:
        llm.elaborate_idea(ALEX, None, "soil sensor", BANK)
    assert (exc.value.status, exc.value.code) == (502, "LLM_REFUSED")
    assert len(messages.requests) == 1


@pytest.mark.parametrize(
    ("error", "code", "retryable"),
    [
        (api_error(429), "LLM_RATE_LIMITED", True),
        (httpx.ReadTimeout("slow"), "LLM_TIMEOUT", True),
        (api_error(504), "LLM_TIMEOUT", True),
        (httpx.ConnectError("down"), "LLM_UNAVAILABLE", True),
        (api_error(401), "LLM_AUTH_FAILED", False),
        (
            genai_errors.ClientError(
                400, {"error": {"message": "API key not valid.", "status": "INVALID_ARGUMENT"}}
            ),
            "LLM_AUTH_FAILED",
            False,
        ),
        (
            genai_errors.ServerError(500, {"error": {"message": "boom", "status": "INTERNAL"}}),
            "LLM_UNAVAILABLE",
            True,
        ),
    ],
)
def test_provider_errors_map_to_503(error, code, retryable):
    llm, messages = provider([error])
    with pytest.raises(AppError) as exc:
        llm.generate_ideas(ALEX, None, None, BANK)
    assert (exc.value.status, exc.value.code, exc.value.retryable) == (503, code, retryable)
    assert len(messages.requests) == 1  # no retry multiplication


def test_bad_request_is_502():
    llm, _ = provider([api_error(400)])
    with pytest.raises(AppError) as exc:
        llm.generate_ideas(ALEX, None, None, BANK)
    assert (exc.value.status, exc.value.code) == (502, "LLM_REQUEST_REJECTED")


def test_blocked_prompt_is_502_without_retry():
    blocked = SimpleNamespace(
        candidates=None, prompt_feedback=SimpleNamespace(block_reason="SAFETY")
    )
    llm, messages = provider([blocked])
    with pytest.raises(AppError) as exc:
        llm.generate_ideas(ALEX, None, None, BANK)
    assert (exc.value.status, exc.value.code) == (502, "LLM_REFUSED")
    assert len(messages.requests) == 1


def test_strict_schema_is_closed_and_unbounded():
    schema = strict_json_schema(ProjectPlanDraft)
    text = json.dumps(schema)
    for key in ('"minItems"', '"maxLength"', '"minimum"', '"default"'):
        assert key not in text

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node["properties"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)


def test_end_to_end_route_in_gemini_mode_with_fake_client(make_client):
    ideas = {
        "ideas": [
            {
                "name": "Plant mood light",
                "summary": "LED shows soil moisture.",
                "suggested_difficulty": None,
                "estimated_total_hours": 10,
                "why_it_fits": "ECE plus plants.",
                "skills_to_learn": ["ADC reading"],
                "assumptions": ["Skill level unknown."],
            }
        ]
    }
    llm, _ = provider([reply(ideas)])
    client = make_client(data_provider=InMemoryProjectDataProvider(), llm_provider=llm)
    body = client.post("/api/users/fixture-ece/chat", json={"mode": "generate_ideas"}).json
    assert body["generation_mode"] == "gemini"
    assert body["ideas"][0]["name"] == "Plant mood light"
    assert "MOCK_GENERATION" not in {w["code"] for w in body["warnings"]}

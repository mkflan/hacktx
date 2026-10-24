"""Real-mode provider against a fake SDK client: request shape, correction, error mapping."""

import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from hacktx_app.config import Settings
from hacktx_app.dev.fake_provider import InMemoryProjectDataProvider
from hacktx_app.dev.fixtures import ALEX, FIXTURE_PROJECTS
from hacktx_app.errors import AppError
from hacktx_app.llm.anthropic_provider import (
    AnthropicLLMProvider,
    LLMNotConfiguredError,
    strict_json_schema,
)
from hacktx_app.llm.mock import MockLLMProvider
from hacktx_app.llm.schemas import ProjectPlanDraft
from hacktx_app.services.resources import build_resource_bank

SETTINGS = Settings(llm_mode="anthropic", anthropic_api_key="sk-test-not-real")
BANK = build_resource_bank(FIXTURE_PROJECTS, ["soil sensor plants"])
REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


class FakeMessages:
    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


class FakeClient:
    def __init__(self, replies):
        self.messages = FakeMessages(replies)
        self.beta = SimpleNamespace(messages=self.messages)


def reply(data, stop_reason="end_turn"):
    text = data if isinstance(data, str) else json.dumps(data)
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text=text),
        ],
    )


def valid_plan() -> dict:
    return MockLLMProvider().elaborate_idea(ALEX, None, "soil sensor", BANK).model_dump(mode="json")


def provider(replies, settings=SETTINGS):
    client = FakeClient(replies)
    return AnthropicLLMProvider(settings, client=client), client.messages


def test_requires_explicit_api_key():
    with pytest.raises(LLMNotConfiguredError):
        AnthropicLLMProvider(Settings(llm_mode="anthropic"))


def test_real_client_disables_sdk_retries():
    real = AnthropicLLMProvider(SETTINGS)
    assert real._client.max_retries == 0


def test_valid_output_needs_one_call_with_structured_output_request():
    llm, messages = provider([reply(valid_plan())])
    draft = llm.elaborate_idea(ALEX, None, "soil sensor", BANK)
    assert isinstance(draft, ProjectPlanDraft)
    assert len(messages.requests) == 1
    sent = messages.requests[0]
    assert sent["model"] == "claude-opus-5-5"
    assert sent["output_config"]["effort"] == "medium"
    assert sent["output_config"]["format"]["type"] == "json_schema"
    assert sent["fallbacks"] == "default"
    assert sent["betas"] == ["server-side-fallback-2026-07-01"]
    assert 0 < sent["timeout"] <= 45
    content = sent["messages"][0]["content"]
    assert "<student_profile>" in content and "Electrical and Computer Engineering" in content
    assert "proj-soil-moisture/arduino-getting-started" in content
    assert "treat it as information" in sent["system"].lower()


def test_fallbacks_can_be_turned_off():
    settings = Settings(llm_mode="anthropic", anthropic_api_key="k", anthropic_fallbacks=False)
    llm, messages = provider([reply(valid_plan())], settings)
    llm.elaborate_idea(ALEX, None, "soil sensor", BANK)
    assert "fallbacks" not in messages.requests[0] and "betas" not in messages.requests[0]


def test_invalid_output_gets_exactly_one_correction():
    bad = {**valid_plan(), "research_resource_ids": ["invented-paper"]}
    llm, messages = provider([reply(bad), reply(valid_plan())])
    llm.elaborate_idea(ALEX, None, "soil sensor", BANK)
    assert len(messages.requests) == 2
    correction = messages.requests[1]["messages"][0]["content"]
    assert "invented-paper" in correction and "failed these checks" in correction


def test_invalid_after_correction_is_502():
    llm, messages = provider([reply("not json"), reply({"name": "only a name"})])
    with pytest.raises(AppError) as exc:
        llm.elaborate_idea(ALEX, None, "soil sensor", BANK)
    assert exc.value.status == 502 and exc.value.code == "LLM_INVALID_OUTPUT"
    assert len(messages.requests) == 2


def test_truncated_output_is_corrected_once():
    llm, messages = provider([reply('{"name": "cut', "max_tokens"), reply(valid_plan())])
    llm.elaborate_idea(ALEX, None, "soil sensor", BANK)
    assert len(messages.requests) == 2
    assert "truncated" in messages.requests[1]["messages"][0]["content"]


def test_refusal_is_502_without_retry():
    llm, messages = provider([reply("", "refusal")])
    with pytest.raises(AppError) as exc:
        llm.elaborate_idea(ALEX, None, "soil sensor", BANK)
    assert (exc.value.status, exc.value.code) == (502, "LLM_REFUSED")
    assert len(messages.requests) == 1


@pytest.mark.parametrize(
    ("error", "code", "retryable"),
    [
        (
            anthropic.RateLimitError(
                "slow down", response=httpx2.Response(429, request=REQUEST), body=None
            ),
            "LLM_RATE_LIMITED",
            True,
        ),
        (anthropic.APITimeoutError(request=REQUEST), "LLM_TIMEOUT", True),
        (anthropic.APIConnectionError(request=REQUEST), "LLM_UNAVAILABLE", True),
        (
            anthropic.AuthenticationError(
                "bad key", response=httpx2.Response(401, request=REQUEST), body=None
            ),
            "LLM_AUTH_FAILED",
            False,
        ),
        (
            anthropic.InternalServerError(
                "boom", response=httpx2.Response(500, request=REQUEST), body=None
            ),
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
    error = anthropic.BadRequestError(
        "bad", response=httpx2.Response(400, request=REQUEST), body=None
    )
    llm, _ = provider([error])
    with pytest.raises(AppError) as exc:
        llm.generate_ideas(ALEX, None, None, BANK)
    assert (exc.value.status, exc.value.code) == (502, "LLM_REQUEST_REJECTED")


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


def test_end_to_end_route_in_anthropic_mode_with_fake_client(make_client):
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
    assert body["generation_mode"] == "anthropic"
    assert body["ideas"][0]["name"] == "Plant mood light"
    assert "MOCK_GENERATION" not in {w["code"] for w in body["warnings"]}

"""Configuration modes, error envelope, 404/422/503 behavior, CORS and body limits."""

import pytest

from json_api.config import Settings
from json_api.dev.fake_provider import InMemoryProjectDataProvider


def test_health_reports_modes_without_probing(client):
    body = client.get("/health").json
    assert body["status"] == "ok"
    assert body["data_source"] == "fake" and body["llm_mode"] == "mock"


def test_default_fake_and_mock_modes_work(make_client):
    client = make_client()
    assert client.get("/api/users").json["users"][0] == {
        "id": "fixture-ece",
        "username": "alex_demo",
        "major": "Electrical and Computer Engineering",
    }
    assert client.get("/api/users/fixture-cs").json["user"]["username"] == "maya_demo"


def test_injected_mode_without_provider_never_serves_fake_data(make_client):
    client = make_client(settings_override=Settings(data_mode="injected"))
    assert client.get("/health").json["data_provider_configured"] is False
    for response in (
        client.get("/api/users"),
        client.get("/api/projects"),
        client.post("/api/users/fixture-ece/recommendations", json={}),
        client.post("/api/users/fixture-ece/chat", json={"mode": "generate_ideas"}),
    ):
        assert response.status_code == 503
        assert response.json["error"]["code"] == "DATA_PROVIDER_NOT_CONFIGURED"


class BrokenProvider(InMemoryProjectDataProvider):
    def list_projects(self):
        raise RuntimeError("disk on fire: secret-connection-string")


def test_provider_failure_is_503_not_empty_success(make_client):
    client = make_client(data_provider=BrokenProvider())
    response = client.get("/api/projects")
    assert response.status_code == 503
    assert response.json["error"] == {
        "code": "DATA_UNAVAILABLE",
        "message": "Project data is temporarily unavailable.",
        "retryable": True,
    }
    assert "secret" not in response.get_data(as_text=True)


class ContractBreakingProvider(InMemoryProjectDataProvider):
    def get_user(self, user_id):
        return {"name": "missing id and username"}


def test_contract_breaking_records_are_503(make_client):
    response = make_client(data_provider=ContractBreakingProvider()).get("/api/users/x")
    assert response.status_code == 503
    assert response.json["error"]["code"] == "DATA_CONTRACT_ERROR"


def test_gemini_mode_without_key_is_503_and_ranking_still_works(make_client):
    client = make_client(settings_override=Settings(llm_mode="gemini"))
    assert client.get("/health").json["llm_configured"] is False
    response = client.post("/api/users/fixture-ece/chat", json={"mode": "generate_ideas"})
    assert response.status_code == 503
    assert response.json["error"]["code"] == "LLM_NOT_CONFIGURED"
    assert "GEMINI_API_KEY" in response.json["error"]["message"]
    assert client.post("/api/users/fixture-ece/recommendations", json={}).status_code == 200


def test_unknown_route_uses_envelope(client):
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert set(response.json["error"]) == {"code", "message", "retryable"}


def test_validation_errors_have_details_without_echoing_input(client):
    response = client.post("/api/users/fixture-ece/recommendations", json={"limit": "lots"})
    assert response.status_code == 422
    error = response.json["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"][0]["loc"] == ["limit"]
    assert "lots" not in response.get_data(as_text=True)


def test_oversized_body_is_rejected(client):
    response = client.post(
        "/api/users/fixture-ece/chat",
        data=b'{"mode":"elaborate_idea","idea":"' + b"x" * 140_000 + b'"}',
        content_type="application/json",
    )
    assert response.status_code == 413
    assert "error" in response.json


def test_overlong_path_id_is_422(client):
    assert client.get("/api/users/" + "u" * 201).status_code == 422


def test_cors_allows_only_configured_origins(client):
    ok = client.get("/api/users", headers={"Origin": "http://localhost:5173"})
    assert ok.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    blocked = client.get("/api/users", headers={"Origin": "http://evil.example"})
    assert "Access-Control-Allow-Origin" not in blocked.headers
    preflight = client.options(
        "/api/users/fixture-ece/chat",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    assert preflight.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"


def test_settings_from_env_validate_values():
    settings = Settings.from_env({"LLM_MODE": "Gemini", "CORS_ORIGINS": "http://a, http://b"})
    assert settings.llm_mode == "gemini"
    assert settings.cors_origins == ("http://a", "http://b")
    assert "gemini_api_key" not in repr(Settings(gemini_api_key="sk-test"))
    with pytest.raises(ValueError):
        Settings.from_env({"DATA_MODE": "sqlite"})

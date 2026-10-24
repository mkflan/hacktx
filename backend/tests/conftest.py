"""Shared test helpers. No SQLite, no network, no paid calls: everything is injected."""

import pytest

from json_api import create_app
from json_api.config import Settings
from json_api.dev.fake_provider import InMemoryProjectDataProvider
from json_api.llm.mock import MockLLMProvider


class SpyLLM:
    """Wraps the mock provider and records every call (and the user it received)."""

    def __init__(self, inner=None, mode: str = "mock", model_id: str = "spy-v1") -> None:
        self.inner = inner or MockLLMProvider()
        self.mode = mode
        self.model_id = model_id
        self.calls: list[tuple[str, dict]] = []

    def generate_ideas(self, user, preferences, topic, resource_bank, limit=3):
        self.calls.append(("generate_ideas", locals()))
        return self.inner.generate_ideas(user, preferences, topic, resource_bank, limit)

    def elaborate_idea(self, user, preferences, idea, resource_bank):
        self.calls.append(("elaborate_idea", locals()))
        return self.inner.elaborate_idea(user, preferences, idea, resource_bank)

    def personalize_project(self, user, preferences, project, resource_bank):
        self.calls.append(("personalize_project", locals()))
        return self.inner.personalize_project(user, preferences, project, resource_bank)


class ExplodingLLM:
    """Fails the test if anything calls the LLM."""

    mode = "mock"
    model_id = "exploding"

    def __getattr__(self, name):
        raise AssertionError(f"LLM must not be called (attempted {name})")


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def data() -> InMemoryProjectDataProvider:
    return InMemoryProjectDataProvider()


@pytest.fixture
def spy() -> SpyLLM:
    return SpyLLM()


@pytest.fixture
def make_client(settings):
    def _make(data_provider=None, llm_provider=None, settings_override=None):
        app = create_app(
            data_provider=data_provider,
            llm_provider=llm_provider,
            settings=settings_override or settings,
        )
        app.testing = True
        return app.test_client()

    return _make


@pytest.fixture
def client(make_client, data, spy):
    return make_client(data_provider=data, llm_provider=spy)

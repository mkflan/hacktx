# Scratchpad: HackTX 26 backend (2026-10-24)

Task: implement application/backend logic from hacktx-claude-code-prompt.md (database-independent).
Repo state at start: only README.md + LICENSE, remote mkflan/hacktx, branches master/backend/front all at ee94c9f.

## Plan (waiting for "go")
1. Project hygiene: CLAUDE.md, .gitignore, .claude/settings.json, .vscode (copied from Hackathon), env.example.txt.
2. Python venv at repo root (.venv), backend/requirements.txt pinned: fastapi, uvicorn, pydantic, anthropic,
   python-dotenv, httpx (TestClient), pytest, ruff.
3. backend/app: contracts, config, dependencies, errors, api/{routes,schemas}, services/{normalize,catalog,
   ranking,resources,personalization,chat,cache}, llm/{base,mock,anthropic_provider,validation,prompts/}, dev/{fixtures,fake_provider}.
4. backend/tests: catalog, ranking, chat/personalize, errors/modes, cache, injection swap.
5. README.md + INTEGRATION.md. Smoke test with uvicorn + curl in fake/mock mode.

## Notes

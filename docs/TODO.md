# TODO

What is finished and what still needs doing. Tick items as they land; add new ones at the
bottom of the right section with an owner.

Owners: **App** = application/backend logic (branch `backend-w/o-database`),
**DB** = database teammate, **Front** = frontend, **Team** = anyone.

## Done (2026-10-24, App)

- [x] Repo setup: `.gitignore`, `requirements.txt` (pinned), `env.example.txt`, `pyproject.toml`
      (pytest + ruff), `.vscode/` settings, `.claude/settings.json`, project `CLAUDE.md`
- [x] Data contract: DTOs + 4-method `ProjectDataProvider` ([contracts.py](../backend/hacktx_app/contracts.py))
- [x] One injection seam: `create_app()` / `init_app()` ([main.py](../backend/hacktx_app/main.py))
- [x] In-memory fixtures: Alex, Maya, 10 projects incl. weeks-only, unknown difficulty, no resources
- [x] Explore: filters (AND, aliases, word matching), stable pagination, grouping, facets, details
- [x] Recommendations: explainable score, time-fit rules, optional skill/goal preferences
- [x] Prompt tab: `generate_ideas` and `elaborate_idea`; catalog personalization
- [x] Mock LLM provider (deterministic, labeled `mock`)
- [x] Anthropic provider: structured output, one correction, 45 s total deadline, SDK retries
      off, refusal/truncation/rate-limit/timeout handling, server-side refusal fallback
- [x] Resource grounding: model may only cite supplied resource IDs; research must be research
- [x] Error envelope, 404/422/502/503, request size limit, CORS allow-list
- [x] In-memory TTL cache keyed by content
- [x] 94 tests passing, `ruff check` clean, local smoke test of the demo flow (fake + mock)
- [x] Pre-integration review (2026-10-24), bugs found and fixed with regression tests:
      real-mode schema dropped the milestone `title` field (every live plan would have failed);
      long ideas produced a bogus 422; server-side validation errors were reported as 422;
      text could close its own prompt block; tiny weekly hours crashed the mock schedule
- [x] README.md, INTEGRATION.md

## To do: integration

- [ ] **DB** Answer the open mapping questions in [INTEGRATION.md](INTEGRATION.md#open-mapping-questions-for-the-database-teammate)
- [ ] **DB** Add a time commitment column for users and timeline + resources for projects
- [ ] **DB** Write a `ProjectDataProvider` implementation over SQLite (your module, your queries)
- [ ] **DB** Persist the two demo users (Alex, Maya) and some projects with your own IDs
- [ ] **Team** Call `init_app(app, data_provider=...)` from the Flask app in `backend/app.py`
- [ ] **Team** Merge `backend-w/o-database` with `backend` (no overlapping files today)
- [ ] **App** Re-run the test suite plus a smoke test against the real provider once it exists

## To do: frontend

- [ ] **Front** User selector from `GET /api/users`
- [ ] **Front** Explore tab: `GET /api/projects` + `/facets`, details inline or in a modal
- [ ] **Front** Recommendations tab: show reasons, score components and warnings
- [ ] **Front** Prompt tab: ideas mode, elaborate mode, "elaborate this idea" from a card
- [ ] **Front** "Personalize" action on Explore/Recommendations cards
- [ ] **Front** Drop late responses whose `user_id` is not the selected user
- [ ] **Front** Show `warnings`, `assumptions` and the mock label

## To do: real model and demo

- [ ] **Team** First live Claude call has never happened. The request schema is checked against
      the models offline, but Anthropic's own acceptance of it (size and feature limits) is unproven

- [ ] **Team** Put `ANTHROPIC_API_KEY` in `env.txt`, set `LLM_MODE=anthropic`, try one live call
      (costs money; not done yet, all LLM tests so far use a fake client)
- [ ] **Team** Tune `ANTHROPIC_EFFORT` if live calls are too slow for the demo
- [ ] **Team** Rehearse: Explore -> Alex recommendations -> switch to Maya -> generate ideas ->
      elaborate a student idea into a full guide

## Later (not in the MVL)

- [ ] **DB** Save generated plans / history (responses say `persisted: false` today)
- [ ] **Team** Verified resources (needs real link and content checks, not just URL syntax)

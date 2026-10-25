# TODO

What is finished and what still needs doing. Tick items as they land; add new ones at the
bottom of the right section with an owner.

Owners: **App** = application/backend logic (branch `backend-w/o-database`),
**DB** = database teammate, **Front** = frontend, **Team** = anyone.

## Done (2026-10-24, App)

- [x] Repo setup: `.gitignore`, `requirements.txt` (pinned), `env.example.txt`, `pyproject.toml`
      (pytest + ruff), `.vscode/` settings, `.claude/settings.json`, project `CLAUDE.md`
- [x] Data contract: DTOs + 4-method `ProjectDataProvider` ([contracts.py](../backend/json_api/contracts.py))
- [x] One injection seam: `create_app()` / `init_json_api()` ([main.py](../backend/json_api/main.py))
- [x] In-memory fixtures: Alex, Maya, 10 projects incl. weeks-only, unknown difficulty, no resources
- [x] Explore: filters (AND, aliases, word matching), stable pagination, grouping, facets, details
- [x] Recommendations: explainable score, time-fit rules, optional skill/goal preferences
- [x] Prompt tab: `generate_ideas` and `elaborate_idea`; catalog personalization
- [x] Mock LLM provider (deterministic, labeled `mock`)
- [x] Gemini provider (`gemini-3.8-flash`): structured output, one correction, 45 s total
      deadline, SDK retries off, refusal/truncation/rate-limit/timeout handling
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

- [x] Schema v2: user time commitment; project majors, interests, timeline, difficulty;
      resources table. Old `app.db` files are refused with a clear message
- [x] `seed.sql`: the two demo users and ten projects from the fixtures (idempotent)
- [x] `sqlite_provider.py`: `ProjectDataProvider` over SQLite, `data_source: "sqlite"`
- [x] `app.py` loads `env.txt`, passes the SQLite provider to `init_json_api`, runs on :8000
- [x] Tests on an in-memory database (seed matches fixtures, same ranking as fake mode, 503 on a
      broken connection) plus a smoke run of `app.py` against a real `app.db` (mock LLM)
- [ ] **DB** Kai to review the schema, seed and provider (written on the app side to unblock the
      demo; see INTEGRATION.md)
- [ ] **DB** Write paths (create users, add projects) if the demo needs them; none exist yet
- [x] Forum (schema v3): `posts` and `comments` tables, demo seed rows, `backend/forum.py`,
      `/forum` page with "post as" demo user picker, tests on an in-memory database
- [x] Removed the "Freetail Hackers" footer credit

## To do: frontend

- [ ] **Front** User selector from `GET /api/users`
- [ ] **Front** Explore tab: `GET /api/projects` + `/facets`, details inline or in a modal
- [ ] **Front** Recommendations tab: show reasons, score components and warnings
- [ ] **Front** Prompt tab: ideas mode, elaborate mode, "elaborate this idea" from a card
- [ ] **Front** "Personalize" action on Explore/Recommendations cards
- [ ] **Front** Drop late responses whose `user_id` is not the selected user
- [ ] **Front** Show `warnings`, `assumptions` and the mock label

## To do: real model and demo

- [x] First live Gemini calls (2026-10-24) through `app.py` + SQLite on `gemini-3.6-flash`:
      generate_ideas 200 in 9 s, elaborate_idea 200 in 19 s; the schema is accepted
- [ ] **Team** `gemini-3.8-flash` (the default) answered `503 high demand` or timed out at 45 s
      every time on 2026-10-24. If that continues, set `GEMINI_MODEL=gemini-3.6-flash` in `env.txt`
- [ ] **Team** Set `LLM_MODE=gemini` in `env.txt` (it is still `mock`)
- [ ] **Team** Tune `GEMINI_THINKING` if live calls are too slow for the demo
- [ ] **Team** Rehearse: Explore -> Alex recommendations -> switch to Maya -> generate ideas ->
      elaborate a student idea into a full guide

## Later (not in the MVL)

- [ ] **DB** Save generated plans / history (responses say `persisted: false` today)
- [ ] **Team** Verified resources (needs real link and content checks, not just URL syntax)

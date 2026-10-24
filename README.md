# hacktx

HackTX 26 project app backend: helps students find, rank and plan projects.

Three tabs, one shared user selector:

| Tab | What the backend does | LLM? |
|---|---|---|
| Explore | Lists shared catalog projects, filtered and grouped by major or interest | No |
| Recommendations | Ranks catalog projects for the selected user's saved profile, with reasons | No |
| Prompt | Generates new idea cards, or turns a student's idea into a full project plan | Yes |

Project details open inside the current tab. A card can also be **personalized**: the catalog
project is loaded and a tailored plan is generated for the selected user, without changing the
shared record.

This branch holds the **application logic only**. SQLite, schema, queries and seeds belong to
the database teammate (see [INTEGRATION.md](docs/INTEGRATION.md)). Until their provider is plugged
in, the app runs on clearly labeled in-memory fixtures (`data_source: "fake"`). Task status is
tracked in [TODO.md](docs/TODO.md).

## Layout

```
backend/hacktx_app/        application package (Flask + Pydantic v2)
  main.py                  create_app() / init_app(): the one place providers are injected
  contracts.py             DTOs + ProjectDataProvider (4 read-only methods)
  dependencies.py          provider access, 503 wrapping for data failures
  api/routes.py, schemas.py
  services/                catalog, ranking, timefit, normalize, resources, generation, cache
  llm/                     base (interface), mock, anthropic_provider, validation, prompts/
  dev/                     fixtures + InMemoryProjectDataProvider (not database seeds)
backend/tests/             pytest, no database and no network
```

## Setup (Windows, Python 3.14)

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Run

```powershell
cd backend
..\.venv\Scripts\python -m hacktx_app        # http://127.0.0.1:8000
```

Tests and lint, from the repo root:

```powershell
.venv\Scripts\python -m pytest
.venv\Scripts\ruff check backend
```

## Modes

Settings come from environment variables, or `env.txt` / `.env` in the repo root (both
gitignored; copy `env.example.txt`).

| Variable | Values | Default | Meaning |
|---|---|---|---|
| `DATA_MODE` | `fake`, `injected` | `fake` | `fake` uses the in-memory fixtures. `injected` needs a provider passed to `init_app()`; without one every data route returns `503 DATA_PROVIDER_NOT_CONFIGURED`. It never falls back to fake data. |
| `LLM_MODE` | `mock`, `anthropic` | `mock` | `mock` is a deterministic offline generator labeled `generation_mode: "mock"`. `anthropic` calls Claude. |
| `ANTHROPIC_API_KEY` | key | none | Required for `LLM_MODE=anthropic`. Server-side only, never sent to the browser. A Claude Code login does not count. |
| `ANTHROPIC_MODEL` | model ID | `claude-opus-5-5` | |
| `ANTHROPIC_EFFORT` | `low`..`max` | `medium` | Lower is faster and cheaper. |
| `ANTHROPIC_FALLBACKS` | `true`, `false` | `true` | Sends Anthropic's server-side refusal fallback (`fallbacks: "default"`), so a safety decline is retried on another model inside the same call. |
| `LLM_DEADLINE_SECONDS` | 5-300 | `45` | Total budget per action, including the single correction retry. |
| `CORS_ORIGINS` | comma list | localhost 3000/5173 | Browser origins allowed to call the API. |

Real-mode failures are explicit: no key or provider down returns 503, invalid output after one
correction returns 502. There is no silent fallback to mock.

## Demo flow (curl)

Use Git Bash, or `curl.exe` in PowerShell (`curl` there is a different command).

```bash
B=http://127.0.0.1:8000
curl -s $B/health
curl -s $B/api/users                                      # user selector

# Explore
curl -s "$B/api/projects?group_by=interest&major=ECE&limit=30&offset=0"
curl -s $B/api/projects/facets
curl -s $B/api/projects/proj-soil-moisture

# Recommendations: Alex, then switch to Maya
curl -s -X POST $B/api/users/fixture-ece/recommendations -H "Content-Type: application/json" -d '{}'
curl -s -X POST $B/api/users/fixture-cs/recommendations -H "Content-Type: application/json" \
  -d '{"limit":3,"preferences":{"skill_level":"beginner"}}'

# Prompt: new ideas, then elaborate the student's own idea into a full plan
curl -s -X POST $B/api/users/fixture-cs/chat -H "Content-Type: application/json" \
  -d '{"mode":"generate_ideas","topic":"Japanese kanji","limit":3}'
curl -s -X POST $B/api/users/fixture-cs/chat -H "Content-Type: application/json" \
  -d '{"mode":"elaborate_idea","idea":"A web app that quizzes me on kanji and charts my progress"}'

# Personalize a catalog card for the selected user
curl -s -X POST $B/api/users/fixture-ece/projects/proj-soil-moisture/personalize \
  -H "Content-Type: application/json" -d '{"preferences":{"budget_usd":30}}'
```

To elaborate a generated idea card, send its `name` and `summary` as the `idea` text.

## API

| Method and path | Body | Returns |
|---|---|---|
| `GET /health` | | modes, whether providers are configured (no database or model probe) |
| `GET /api/users` | | `{users:[{id,username,major}], data_source}` |
| `GET /api/users/{user_id}` | | `{user, data_source}` |
| `GET /api/projects` | query: `group_by=major\|interest`, `major`, `interest`, `difficulty`, `limit` 1-100, `offset` | `{groups:[{key,label,projects}], total, limit, offset, data_source, warnings}` |
| `GET /api/projects/facets` | | majors, interests, difficulties (with counts) from the data |
| `GET /api/projects/{project_id}` | | `{project, missing_details, warnings, data_source}` |
| `POST /api/users/{user_id}/recommendations` | `{limit?:1-3, preferences?}` | `{user_id, projects:[RecommendationCard], data_source, warnings}` |
| `POST /api/users/{user_id}/chat` | `{mode:"generate_ideas", topic?, limit?, preferences?}` | `{mode, user_id, ideas, generation_mode, data_source, persisted:false, warnings, cache_hit}` |
| | `{mode:"elaborate_idea", idea, preferences?}` | `{mode, user_id, original_idea, project:ProjectPlan, generation_mode, data_source, persisted:false, warnings, cache_hit}` |
| `POST /api/users/{user_id}/projects/{project_id}/personalize` | `{preferences?}` | `{user_id, source_project_id, project:ProjectPlan, generation_mode, data_source, persisted:false, warnings, cache_hit}` |

`preferences` (all optional, used only for that request, never saved): `skill_level`
(beginner/intermediate/advanced), `technical_goals` (up to 10), `existing_skills` (up to 20),
`budget_usd` (at least 0), `available_materials` (up to 20). Unknown fields anywhere in a body
or query are rejected with 422, so a body can never replace the saved major, interests or time.

Filters: `major` and `interest` are case-insensitive, handle aliases (ECE, CS, ME) and match
tag words ("sensor" matches "sensors"). All filters combine with AND. Pagination runs over
unique projects in stable ID order before grouping, so a project with two majors can appear in
two groups but counts once in `total`. Projects with unknown difficulty appear without a
difficulty filter and are left out (with a warning) when one is applied.

Example recommendation card (trimmed):

```json
{
  "project": {"id": "proj-soil-moisture", "name": "Smart Soil Moisture Monitor", "...": "..."},
  "score": 7.0,
  "score_components": {"major_match": 1.0, "interest_overlap": 0.67, "time_fit_bonus": 2.0, "preference_bonus": 0.0},
  "matched_majors": ["Electrical and Computer Engineering"],
  "matched_interests": ["sensors", "plants"],
  "time_fit": {"status": "fits", "explanation": "Estimated 10 total hours fits your 12 total hours."},
  "reasons": ["Matches your major (...).", "Shares your interests: sensors, plants.", "..."],
  "warnings": []
}
```

The score is a readable heuristic, not a probability:
`3*major_match + 3*interest_overlap + time_fit_bonus (0 or 2) + preference_bonus`.
Projects whose known total hours exceed a known total-hours budget are excluded. A
`hours_per_week` budget is not a total cap: those cards show an estimated number of weeks
instead. Weeks are never converted to hours.

A `ProjectPlan` has: name, summary, suggested majors/interests, difficulty (nullable) with
assumptions, deliverable, learning objectives, prerequisites, estimated total hours, a weekly
schedule, estimated cost (nullable), materials and software, 4-8 milestones (objective, steps,
expected output, definition of done, pitfalls, hours, resource IDs), `resources`,
`research_connections`, `similar_examples`, 3 customization ideas, success criteria, first
action, scope adjustments, constraint warnings, assumptions and `suggested_search_queries`.
Resource lists only ever contain records supplied by the data provider; the model can only
pick their IDs. When nothing fits, the lists are empty, a warning says so, and search queries
are offered as suggestions.

Errors always look like `{"error": {"code", "message", "retryable"}}` (422 adds `details`).
Codes include `USER_NOT_FOUND`, `PROJECT_NOT_FOUND` (404), `VALIDATION_ERROR` (422),
`DATA_PROVIDER_NOT_CONFIGURED`, `DATA_UNAVAILABLE`, `LLM_NOT_CONFIGURED`, `LLM_RATE_LIMITED`,
`LLM_TIMEOUT`, `LLM_UNAVAILABLE` (503), and `LLM_INVALID_OUTPUT`, `LLM_REFUSED` (502).

## Frontend notes

- Keep the selected `user_id` in the browser if you like; profile values always come from the
  server.
- Personalized responses include `user_id`. When the user switches, ignore any late response
  whose `user_id` is not the currently selected user (or cancel it with `AbortController`).
- Show `warnings` and `assumptions`; they carry the honesty labels (mock output, unverified
  links, unknown time or difficulty).
- `persisted` is always `false`: generated plans are not saved anywhere yet.

## Caching

Valid generated responses are cached in memory (100 entries, 15 minutes). The key is a hash of
the actual user record, preferences, idea or project, resource bank, prompt version, model and
mode, so editing a profile changes the key. The cache is lost on restart, and two identical
requests sent at the same moment may both reach the model.

## Not done here

This branch does not implement or verify a SQLite integration, persisted demo users, saved
generated projects or persistence across restarts. Those are the database teammate's work and
are listed in [TODO.md](docs/TODO.md).

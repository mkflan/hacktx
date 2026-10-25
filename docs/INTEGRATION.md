# Integration handoff: database and application

## Folder map: what is what

Two separate pieces live in `backend/`. They are connected in one place (`app.py`).

| Path | What it is | Owner |
|---|---|---|
| `backend/app.py` | The Flask web app: page routes such as `/` and `/dashboard/<user_id>` that serve populated pages to the user | Database / Flask teammate |
| `backend/db.py`, `backend/schema.sql`, `backend/seed.sql` | SQLite connection, schema (version 2) and demo rows | Database / Flask teammate |
| `backend/sqlite_provider.py` | The SQLite `ProjectDataProvider`: read-only queries and the row-to-DTO mapping | Database / Flask teammate |
| `backend/json_api/` | The JSON integration layer: `/api/...` endpoints, ranking, LLM generation and the `ProjectDataProvider` contract. It returns JSON only and never renders pages or opens SQLite | Application |
| `backend/json_api/dev/` | Fake data for tests and local demos only | Application |
| `backend/tests/` | Tests for `json_api` (fake data and fake LLM, no database, no network) | Application |
| `docs/INTEGRATION.md` | This file | Both |
| `docs/TODO.md` | Task status | Both |

How they connect: `app.py` calls
`init_json_api(app, data_provider=SQLiteProjectDataProvider(db.get_db))`, which adds the
`/api/...` routes to the Flask app, reading SQLite through one connection per request. Page
routes such as `/dashboard/<user_id>` call `json_api.services` directly instead of going through
HTTP. `DATA_MODE=fake` swaps in the in-memory fixtures. `python -m json_api` (from `backend/`)
still runs the JSON API alone on fixtures.

Note: the schema, seed and provider were written on the application side (Rashmi and Viraj's
decision) to unblock the demo. Kai: please review them and change anything; the tests in
`backend/tests/test_sqlite_provider.py` will tell you if the mapping still fits the contract.

## Who owns what

| Area | Owner |
|---|---|
| SQLite schema, tables, connections, queries, migrations, seeds, database files | Database teammate |
| User/project read functions and their mapping into the DTOs below | Database teammate |
| Saving generated plans or history (future) | Database teammate |
| The `ProjectDataProvider` contract, DTOs, services, routes, ranking, LLM calls | Application (this branch) |

The application never opens SQLite, imports `sqlite3`, or assumes a table layout. It only calls
the four methods below.

## The contract: four read-only methods

Defined in [backend/json_api/contracts.py](../backend/json_api/contracts.py):

```python
class ProjectDataProvider(Protocol):
    def list_users(self) -> list[NormalizedUser]: ...
    def get_user(self, user_id: str) -> NormalizedUser | None: ...
    def list_projects(self) -> list[NormalizedProject]: ...
    def get_project(self, project_id: str) -> NormalizedProject | None: ...
```

- Return `None` for an unknown ID (the app turns that into 404).
- Raise for real failures (locked database, bad connection). The app turns any exception into
  `503 DATA_UNAVAILABLE` and logs it; it never shows an empty catalog as success.
- Returning plain dicts in the DTO shape also works (they are validated); anything that does
  not fit returns `503 DATA_CONTRACT_ERROR`.
- `list_projects()` returning the whole catalog is fine at hackathon size; the app filters
  and paginates.
- Optionally set `data_source = "sqlite"` (or similar) on your class; it is echoed in
  responses. Without it, responses say `"injected"`.

## Plugging it in (one place)

Your Flask app (`backend/app.py` on the `backend` branch) can mount everything with one call:

```python
from json_api import init_json_api
from your_module import YourProjectDataProvider   # your code, your queries

init_json_api(app, data_provider=YourProjectDataProvider())
```

`init_json_api` registers the routes, error handlers and CORS on your existing app. Because routes
run inside a Flask request, your `db.get_db()` (which uses `g` and `current_app`) works inside
the provider methods. Standalone, `create_app(data_provider=..., llm_provider=...)` does the
same with a new Flask app. With `DATA_MODE=injected` and no provider passed, the data routes
return `503 DATA_PROVIDER_NOT_CONFIGURED`.

Note: the skeleton's `/dashboard/<user_id>` route and these `/api/...` routes don't collide.
The skeleton imports `db` as a top-level module, so run it from `backend/`; this package is
importable from there too.

## Normalized shapes, with examples

All IDs are opaque strings. Integer IDs are accepted and turned into strings (`7` becomes
`"7"`). Do not make IDs from display names.

```json
{
  "id": "7",
  "username": "alex_demo",
  "major": "Electrical and Computer Engineering",
  "interests": ["sensors", "plants", "sustainability"],
  "time_commitment": {"raw": "12 total hours", "amount": 12, "unit": "total_hours", "estimated_total_hours": 12}
}
```

```json
{
  "id": "101",
  "name": "Smart Soil Moisture Monitor",
  "associated_majors": ["Electrical and Computer Engineering"],
  "interests": ["sensors", "plants", "IoT"],
  "timeline": {"raw": "10 total hours", "amount": 10, "unit": "total_hours", "estimated_total_hours": 10},
  "resources": [
    {"id": "101/r1", "title": "Getting Started with Arduino",
     "url": "https://docs.arduino.cc/learn/starting-guide/getting-started-arduino/",
     "kind": "documentation", "provider": "Arduino", "topic_tags": ["arduino"],
     "verification_status": "provided_unverified", "content_excerpt": null, "metadata": {}},
    {"id": "101/r2", "title": "Wiring notes", "url": null, "kind": "guide",
     "content_excerpt": "Power the sensor from 3.3 V ...", "verification_status": "provided_unverified"}
  ],
  "description": "Optional. Null is fine.",
  "difficulty": null
}
```

Required: user `id` and `username`; project `id` and `name`. Everything else has a safe empty
default, and the app reports what is missing instead of guessing.

### TimeValue

`{raw, amount, unit, estimated_total_hours}` with `unit` one of:

| unit | Example | How the app uses it |
|---|---|---|
| `total_hours` | `{"amount": 12, "unit": "total_hours"}` | A hard total. `estimated_total_hours` is filled from `amount`. Projects over a user's total are excluded. |
| `hours_per_week` | `{"amount": 5, "unit": "hours_per_week"}` | Weekly availability, not a cap. Shows estimated weeks for projects with known total hours. |
| `weeks` | `{"amount": 6, "unit": "weeks"}` | Calendar span only. Never converted to work hours. Add `estimated_total_hours` only if the source states the workload. |
| `unknown` | `{"raw": "a few weekends", "unit": "unknown"}` | Kept as text; scored as unknown, with a warning. |

### Resource

`kind` is one of guide, research, tutorial, documentation, example, other. Use `url: null`
plus `content_excerpt` for a text guide; never invent a URL. `verification_status` stays
`provided_unverified` unless you have real evidence a link and its content were checked (a URL
that parses is not evidence). Resource IDs must be stable, and may be scoped under the project
ID (`101/r1`). `metadata` (author, year, DOI) is optional and only for values a real source
supplied.

## How the SQLite tables map (schema version 2)

| Column | DTO field | Rule |
|---|---|---|
| `users.id`, `projects.id` (integers) | `id` | Sent as strings (`"1"`). A non-numeric ID is simply not found (404). |
| `users.interests`, `projects.majors`, `projects.interests`, `resources.topic_tags` | lists | Comma-separated text, trimmed; empty parts and duplicates dropped. Items cannot contain commas. |
| `users.time_amount/unit/raw` | `time_commitment` | Unit is `total_hours`, `hours_per_week`, `weeks` or `unknown` (a `CHECK` constraint). |
| `projects.timeline_*` | `timeline` | Same units. `timeline_estimated_hours` only when the source states the workload; `total_hours` fills it itself. |
| `projects.scope` | `description` | Nullable. |
| `projects.difficulty` | `difficulty` | `beginner`, `intermediate`, `advanced` or NULL. |
| `resources (project_id, slug)` | `resources[].id` | `"<project_id>/<slug>"`, stable as long as the slug is. `url` NULL plus `content_excerpt` is a text guide. |

`schema.sql` stamps the database with `PRAGMA user_version = 2`. An `app.db` made by the first
skeleton (version 0) is refused with a message to delete it, instead of failing on missing
columns later. Real migrations are not needed yet: `app.db` only holds local dev data.

## Fields that are not database columns

`skill_level`, `technical_goals`, `existing_skills`, `budget_usd` and `available_materials`
arrive per request as optional `preferences`. They are not stored and need no schema change.
When missing, generated plans state their assumptions and ranking does not use difficulty.
`difficulty` and `description` on projects are optional; null is handled.

## Demo data

`seed.sql` inserts the two fictional students and the ten sample projects from
[fixtures.py](../backend/json_api/dev/fixtures.py) with fixed IDs and `INSERT OR IGNORE`, so it
runs safely on every start (`app.config["SEED_DEMO_DATA"] = False` turns it off). It was
generated from the fixtures, so both modes show the same demo:

| ID | username | major | time commitment |
|---|---|---|---|
| `1` | alex_demo | Electrical and Computer Engineering | 12 total hours |
| `2` | maya_demo | Computer Science | 20 total hours |

The fixture IDs `fixture-ece` and `fixture-cs` exist only in fake mode. The frontend should
always take IDs from `GET /api/users`.

## Saving generated plans

Every generated response returns `persisted: false`. Nothing is saved, and no save method is
called. Saving or history would be a later, separate integration (for example a
`save_plan(user_id, plan)` method you own). The current endpoints do not depend on it.

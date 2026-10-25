# hacktx: HackTX 26 project (Hackathon project)

This repo is the hackathon project. The parent `Documents\GitHub\CLAUDE.md` and
`Documents\GitHub\Hackathon\CLAUDE.md` rules apply here: plan first and wait for "go", the
folder layout, small commits, secrets in `env.txt`, and handoffs.

## Layout
- `backend/app.py`: the Flask app (`create_app()`, page routes). `frontend/templates/`,
  `frontend/static/`: Jinja pages and static files.
- `backend/db.py`, `schema.sql`, `seed.sql`, `sqlite_provider.py`: SQLite.
- `backend/json_api/`: JSON API, ranking and Gemini (Flask + Pydantic v2). `backend/tests/`: pytest.
- `docs/`: INTEGRATION.md (how the pieces connect) and TODO.md (task status). Nothing else
  loose in the root.
- `temp/`: scratch files and scratchpad (gitignored).

## Branches
- `master` is the main line. Do feature work on a branch and merge it into `master` when tests
  pass. Do not switch branches over someone's uncommitted changes.
- Never push or deploy unless asked.

## Layer rules
- Rashmi and Viraj own the whole backend, including the schema, seed and provider (Kai handed
  them over on 2026-10-24).
- All SQL stays in `db.py`, `schema.sql`, `seed.sql` and `sqlite_provider.py`. Never import
  `sqlite3`/ORMs in `backend/json_api/`, and never commit `app.db`.
- Data reaches json_api only through `ProjectDataProvider` (4 read methods) injected via
  `init_json_api()` / `create_app()`. A table change updates `sqlite_provider.py` and the
  schema version in the same commit. See docs/INTEGRATION.md.

## Commands
- Tests: `.venv\Scripts\python -m pytest` (repo root). Lint: `.venv\Scripts\ruff check backend`.
- Run: `cd backend` then `..\.venv\Scripts\python app.py` (127.0.0.1:8000, SQLite).
- Tests use fake LLM providers and fake or in-memory SQLite data only: no database file, no
  network, no paid calls.

## Rules for generated content
- Never invent URLs, papers or citations in fixtures or prompts. The model may only cite
  supplied resource IDs.
- Label fake data (`data_source`) and mock output (`generation_mode`) honestly; no silent
  fallbacks.
- Task status lives in docs/TODO.md: update it when something lands.

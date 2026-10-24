# hacktx: HackTX 26 project (Hackathon project)

This repo is the hackathon project. The parent `Documents\GitHub\CLAUDE.md` and
`Documents\GitHub\Hackathon\CLAUDE.md` rules apply here: plan first and wait for "go", the
folder layout, small commits, secrets in `env.txt`, and handoffs.

## Layout
- `backend/json_api/`: application logic (Flask + Pydantic v2). `backend/tests/`: pytest.
- `docs/`: INTEGRATION.md (database handoff) and TODO.md (task status). Nothing else loose in the root.
- `temp/`: scratch files and scratchpad (gitignored).

## Branches
- `backend-w/o-database`: application logic (this work). `backend`: teammate's Flask + SQLite
  skeleton. `front`: frontend. Do not switch branches over someone's uncommitted changes.
- Never push or deploy unless asked.

## Ownership boundary
- Do not create or edit SQLite schema, queries, migrations, seeds, `db.py`, `schema.sql` or
  database files. Do not import `sqlite3`/ORMs in `backend/json_api/`.
- Data reaches the app only through `ProjectDataProvider` (4 read methods) injected via
  `init_app()` / `create_app()`. See docs/INTEGRATION.md.

## Commands
- Tests: `.venv\Scripts\python -m pytest` (repo root). Lint: `.venv\Scripts\ruff check backend`.
- Run: `cd backend` then `..\.venv\Scripts\python -m json_api` (127.0.0.1:8000).
- Tests use fake data and fake LLM providers only: no database, no network, no paid calls.

## Rules for generated content
- Never invent URLs, papers or citations in fixtures or prompts. The model may only cite
  supplied resource IDs.
- Label fake data (`data_source`) and mock output (`generation_mode`) honestly; no silent
  fallbacks.
- Task status lives in docs/TODO.md: update it when something lands.

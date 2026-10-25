# hacktx: HackTX 26 project (Hackathon project)

This repo is the hackathon project. The parent `Documents\GitHub\CLAUDE.md` and
`Documents\GitHub\Hackathon\CLAUDE.md` rules apply here: plan first and wait for "go", the
folder layout, small commits, secrets in `env.txt`, and handoffs.

## Layout
- `backend/app.py`: the Flask factory. `backend/pages.py`: HTML routes. `frontend/templates/`,
  `frontend/static/`: Jinja pages and `rabbit.js`.
- `backend/db.py`, `schema.sql`, `seeding.py`, `seed_data/`, `sqlite_provider.py`,
  `profiles.py`, `forum.py`, `enrich.py`: SQLite and the authored seed.
- `backend/serp.py`: SerpApi client + cache; `backend/serp_cache.json`: committed snapshot.
- `backend/json_api/`: JSON API, ranking, Gemini providers, the assistant, search conversions
  (Flask + Pydantic v2). `backend/tests/`: pytest. `scripts/`: enrichment.
- `docs/`: SPEC.md (demo plan), DEMO.md (run sheet), INTEGRATION.md, TODO.md, BACKLOG.md.
  Nothing else loose in the root.
- `temp/`: scratch files and scratchpad (gitignored).

## Branches
- `master` is the main line. Do feature work on a branch and merge it into `master` when tests
  pass. Do not switch branches over someone's uncommitted changes.
- Never push or deploy unless asked.

## Layer rules
- Rashmi and Viraj own the whole backend, including the schema, seed and provider (Kai handed
  them over on 2026-10-24).
- All SQL stays in the backend/ modules listed above. Never import `sqlite3`/ORMs or call
  SerpApi directly in `backend/json_api/`; data, LLM and search are injected providers
  (`init_json_api()` / `create_app()`). Never commit `app.db`.
- A table change updates `sqlite_provider.py` and the schema version in the same commit.
  See docs/INTEGRATION.md.
- SerpApi quota is finite (free plan 250/month): every query goes through the cached client
  and the enrichment script takes a `--max-searches` budget. Never loop over live searches
  without one.

## Commands
- Tests: `.venv\Scripts\python -m pytest` (repo root). Lint: `.venv\Scripts\ruff check backend scripts`.
- Enrich the catalog: `.venv\Scripts\python scripts\enrich_catalog.py --max-searches N`
  (then `--export` to refresh `backend/serp_cache.json`).
- Run: `cd backend` then `..\.venv\Scripts\python app.py` (127.0.0.1:8000, SQLite).
- Tests use fake LLM providers and fake or in-memory SQLite data only: no database file, no
  network, no paid calls.

## Rules for generated content
- Never invent URLs, papers or citations in fixtures or prompts. The model may only cite
  supplied resource IDs.
- Label fake data (`data_source`) and mock output (`generation_mode`) honestly; no silent
  fallbacks.
- Task status lives in docs/TODO.md: update it when something lands.

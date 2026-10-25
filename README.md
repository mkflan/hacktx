# RabbitHole

**Find a project that fits your major, your interests, your time and your level, then get
everything you need to start it: a plan, a shopping list with where to buy, documentation,
tutorials, papers, and a mentor who knows the project.**

Built at HackTX 26 for the SerpApi track. Flask + SQLite + Gemini + SerpApi.

## What it does

1. **Profile in thirty seconds.** The landing pop-up asks for a username, major, interests,
   timeframe and difficulty. No password.
2. **The Rabbit Hole.** A Netflix-style dashboard: the top shelf is ranked for the student
   (major match, interest overlap, time fit, difficulty), then shelves by major, interest,
   difficulty and timeframe over a catalog of 47 projects across 9 majors.
3. **Project pages.** Getting-started outline, materials with store links and prices, and
   grouped sources: documentation, YouTube tutorials, papers. Every link is either written by
   the team or returned by a SerpApi search, and each one says which.
4. **Caterpillar Mentor.** A Gemini mentor in two modes: about one catalog project (it knows the
   outline, materials and sources) or developing the student's own pitch. It may link only to
   sources it was given; anything else is removed before the student sees it. "Dig deeper" runs
   a live SerpApi search mid-conversation.
5. **Project starters.** "Turn into a project starter": SerpApi finds tutorials and papers for
   the idea, Gemini writes the full plan (milestones, materials, schedule, sources), and one
   click posts it to the Wonderland Forum.
6. **Wonderland Forum.** The community forum: starters and discussions, searchable and sortable.

## Where SerpApi does the work

RabbitHole does not make sources up; it digs them up. `backend/serp.py` wraps four SerpApi
engines behind one cached client (the `serp_cache` table, so a query is never paid for twice):

| Engine | Used for |
|---|---|
| `youtube` | tutorials for each project, "Dig deeper", starters |
| `google` | documentation and guides for each project, "Dig deeper" |
| `google_scholar` | papers for intermediate and advanced projects, starters |
| `google_shopping` | where to buy each project's first material, with price and store |

`scripts/enrich_catalog.py` fills the catalog within a search budget; `backend/serp_cache.json`
is the committed snapshot, so a fresh clone rebuilds every found resource offline at zero cost.

## Run it

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy env.example.txt env.txt        # then fill in GEMINI_API_KEY and SERPAPI_API_KEY
cd backend
..\.venv\Scripts\python app.py      # http://127.0.0.1:8000
```

The first start creates `backend/app.db`, seeds the catalog, the demo students and the forum,
and replays `serp_cache.json`. Demo students: `alex_demo` (ECE, beginner, 12 h) and `maya_demo`
(CS, intermediate, 40 h); the Accessibility menu in the nav (text size and test user)
jumps between them. `docs/DEMO.md` is the run sheet.

Tests and lint, from the repo root:

```powershell
.venv\Scripts\python -m pytest       # in-memory SQLite, mock LLM, fake search; no network
.venv\Scripts\ruff check backend scripts
```

## Settings

`env.txt` or `.env` in the repo root (both gitignored; copy `env.example.txt`).

| Variable | Values | Default | Meaning |
|---|---|---|---|
| `LLM_MODE` | `mock`, `gemini` | `mock` | `mock` is a deterministic offline mentor labeled `generation_mode: "mock"`. |
| `GEMINI_API_KEY` | key | none | Required for `LLM_MODE=gemini`. Server-side only. |
| `GEMINI_MODEL` | model ID | `gemini-3.5-flash-lite` | Fast and not overloaded on 2026-10-25 (chat 4 s, starter 9 s). 3.6 and 3.8 Flash returned 503 on and off; 2.5 Flash is no longer served. |
| `GEMINI_FALLBACK_MODEL` | model ID or empty | `gemini-3.6-flash` | Tried once when the main model is unavailable, rate limited or times out. Responses report which model answered. |
| `GEMINI_THINKING` | `minimal`..`high` | `medium` | Lower is faster. |
| `SERPAPI_API_KEY` | key | none | Enables "Dig deeper", starter sources and the enrichment script. Without it the catalog still works from the authored seed and the cache snapshot. |
| `LLM_DEADLINE_SECONDS` | 5-300 | `45` | Total budget per generation, including the one correction retry. |
| `SECRET_KEY` | string | dev default | Signs the cookie that remembers the current student. |
| `DATA_MODE` | `injected`, `fake` | `injected` | `fake` serves json_api's in-memory fixtures instead of SQLite (tests and offline demos). |

## How it works

```
browser ──> pages.py (Jinja) ──> json_api.services ──┐
       └──> /api/... (json_api)                      ├──> ProjectDataProvider = SQLite (sqlite_provider.py)
                                                     ├──> LLMProvider        = Gemini | mock
                                                     └──> SearchProvider     = SerpApi (serp.py) | disabled
```

- `backend/app.py` is the Flask factory. `backend/pages.py` renders `frontend/templates/`.
- `backend/json_api/` is the application core: the `/api/...` routes, explainable ranking, the
  LLM providers and prompts, the Caterpillar (`services/assistant.py`) and the SerpApi result
  conversions (`search.py`). It never opens SQLite or calls SerpApi itself; both are injected.
- `backend/schema.sql`, `db.py`, `seed_data/`, `seeding.py` own the data: schema v4, the
  authored catalog, demo users, forum starters and the search-cache replay.
- Rules the code enforces: generated plans may cite only supplied resource IDs; chat replies
  lose any URL that was not supplied; every search result is labeled `serpapi:<engine>` and
  stays `provided_unverified` (a search hit is not a content check); mock output is labeled.

## Layout

```
backend/app.py            Flask factory: pages + json_api + SQLite + SerpApi wiring
backend/pages.py          landing, profile form, dashboard shelves, project page, chat, forum
backend/profiles.py       the profile write path          backend/forum.py   posts, starters, search
backend/serp.py           SerpApi client, cache, export    backend/enrich.py  store found resources
backend/db.py, schema.sql, seeding.py, seed_data/        schema v4 and the authored seed
backend/serp_cache.json   committed SerpApi snapshot (replayed on first start)
backend/json_api/         routes, ranking, LLM providers + prompts, assistant, search conversions
backend/tests/            pytest; in-memory SQLite, mock LLM, fake search
frontend/templates/       base, index, dashboard, project, chat, forum, post + macros
frontend/static/rabbit.js markdown + plan rendering in the browser
scripts/enrich_catalog.py budgeted SerpApi enrichment of the catalog (--export refreshes the snapshot)
docs/                     SPEC.md, DEMO.md, INTEGRATION.md, TODO.md, BACKLOG.md
```

## Not done

Login, profile editing, saved chat history, verified sources and public deployment: see
`docs/BACKLOG.md`.

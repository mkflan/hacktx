# Handoff: Research Rabbit demo build (HackTX 26)

When: 2026-10-25 00:50 · Paired: Rashmi + Viraj · Branch: master · Last commit: e97bd71 feat: Gemini fallback model, SerpApi cache snapshot

## Goal
A judged demo for the SerpApi track: students get a profile, a Netflix-style project dashboard,
project pages with real sources dug up by SerpApi, a Gemini mentor (the Caterpillar), project
starters posted to the Wonderland forum. Plan in docs/SPEC.md, run sheet in docs/DEMO.md.

## Done this session
- Schema v4 and an authored catalog of 47 projects across 9 majors (outlines, materials,
  guides) in backend/seed_data/; Python seeding; 10 users (2 demo + 8 community).
- Landing pop-up creates or re-enters a profile (cookie session, nav switcher).
- Dashboard shelves (recommended, by major, interest, difficulty, timeframe); project pages
  with materials table, grouped sources, "Make it mine" (Gemini plan), "Dig deeper" (SerpApi).
- The Caterpillar: Gemini chat in project and general mode; replies may link only to supplied
  sources; "Turn into a project starter" -> "Post to Wonderland".
- SerpApi: injectable SearchProvider, cached client (serp_cache), enrichment script run with
  152 searches: 492 found resources + 31 store links; snapshot committed to
  backend/serp_cache.json and replayed on first start (offline-safe).
- Gemini fallback (gemini-3.6-flash -> gemini-2.5-flash) with per-model config.
- 186 tests green, ruff clean. Live checks on 2026-10-25: mentor 6.6 s, starter 26.7 s.

## Current state
- Everything in docs/SPEC.md works locally. backend/app.db (gitignored) holds the enriched
  catalog; deleting it is safe (the snapshot rebuilds it) but costs nothing to keep.
- SerpApi free plan: 89 searches left of 250 as of 00:40. Each "Dig deeper" or starter = 2
  live searches; repeats are cached and free.
- Keys live in .env at the repo root (GEMINI_API_KEY, SERPAPI_API_KEY, LLM_MODE=gemini).
- Four new commits are on local master, not pushed. origin/master is still at 5c42b10.
- A dev server may still be running from the last session on 127.0.0.1:8000; restart it.

## Next steps (in order)
1. Decide whether to push master to origin (`git push origin master`); nothing is pushed yet.
2. Rehearse docs/DEMO.md twice on the demo laptop; time it; fix anything awkward.
3. Record a backup video of the journey in case Wi-Fi or quotas fail.
4. Devpost write-up and the 2-3 minute video script (hackathon playbook, section 4).
5. Optional polish: BACKLOG.md (login, profile editing, saved chat history, deployment).

## Open questions / decisions waiting
- Push to origin/master now, or keep local until after rehearsal?
- Should "Dig deeper" results also be written for the chat page (today only the project page
  persists them; chat results are shown live and cached)?

## Files touched
- backend/seed_data/, seeding.py, schema.sql, db.py: catalog and seeding (v4, replay)
- backend/pages.py, profiles.py, forum.py, enrich.py, serp.py: pages, write paths, SerpApi
- backend/json_api/: contracts, search.py, services/assistant.py, llm/ (chat, fallback), routes
- frontend/templates/*, frontend/static/rabbit.js: all pages
- scripts/enrich_catalog.py, backend/serp_cache.json: enrichment and the offline snapshot
- docs/: SPEC, DEMO, BACKLOG, README, TODO, INTEGRATION, CLAUDE.md

## How to run / test right now
- `cd backend` then `..\.venv\Scripts\python app.py` -> http://127.0.0.1:8000 (use a private
  window so the profile pop-up shows; `/health` must say llm_mode gemini, search_enabled true)
- `.venv\Scripts\python -m pytest` and `.venv\Scripts\ruff check backend scripts` (repo root)
- Refresh the snapshot after more enrichment: `scripts\enrich_catalog.py --export-only`

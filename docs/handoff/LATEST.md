# Handoff: RabbitHole demo polish (rename, accessibility menu, forum identity, Gemini 3.5 Flash-Lite)

When: 2026-10-25 11:10 · Paired: Rashmi + Viraj · Branch: master · Last commit: 3c2299a docs: RabbitHole names, model defaults, SerpApi costs and the accessibility menu in the run sheet

## Goal
RabbitHole (was Research Rabbit), the HackTX 26 SerpApi-track demo: profiles, Netflix-style
project shelves, project pages with SerpApi sources, a Gemini mentor (the Caterpillar), the
Wonderland Forum. Plan in docs/SPEC.md, run sheet in docs/DEMO.md.

## Done this session (Rashmi's punch-list, autonomous run, branch feat/demo-polish merged)
- App renamed RabbitHole everywhere (titles, nav, README, SPEC, DEMO). Tabs: Home, Rabbit Hole
  Projects, Caterpillar Mentor, Wonderland Forum. Landing: "Find Your Next Project" copy and
  "Unearth Your Project Profile". Footer: "Made with ♥ by sudo make us win · HackTX 2026".
- Nav: text size (slider 100-150%) and the test-user switcher sit behind one Accessibility
  button (popover, Escape and outside click close it). The switcher lists every profile, so one
  made on the landing page appears too (was the first 10 users only).
- Forum: no "Comment as" or "Post as" dropdown. Comments and posts are made as the signed-in
  student; a user_id sent in the form is ignored; no profile gives a 400 with a message.
- Project page: "Dig deeper" moved from the right column to under the materials table.
- Gemini: live checks showed gemini-2.5-flash is gone (404 for new users), gemini-3.6-flash
  answered a chat in 10 s but returned 503 on a starter, gemini-3.5-flash-lite did chat in 4 s
  and a starter in 9 s. Defaults are now 3.5-flash-lite first, 3.6-flash as fallback;
  .env GEMINI_MODEL was updated to match (DEMO.md step 1 told it to pin 3.6).
- SerpApi: the "half my quota in one search" was the enrichment script (default budget was 80
  per run; 161 used this month, all enrichment; 89 plan searches + 1000 extra credits left).
  A budget-20 default and balance check were added, then reverted at Rashmi's request (she saw
  lower search quality); the script is back to its original default of 80.
  Per action: dig 2, starter 2, mentor turn with dig 2; repeats free.
- Text size in the Accessibility menu is a minus / plus pair (100-150%, steps of 10).
- Tests: 196 pass (15 new or changed, written first). ruff clean. Pages checked in a browser.

## Current state
- master == feat/demo-polish (fast-forward). Nothing pushed; origin/master is at 3f796de.
- A dev server was started on http://127.0.0.1:8000 from master (and a stray one on :8010).
  Stale app.py processes were killed to restart cleanly, including one from 10:18 that was
  probably Rashmi's own server: restart yours with `cd backend` + `..\.venv\Scripts\python app.py`.
- Pre-existing browser console 404 for /tailwindcss (the @import in base.html); harmless.

## Next steps (in order)
1. Review the four commits (cd0f855..3c2299a) and push to origin if happy (not pushed).
2. Rehearse docs/DEMO.md twice on the demo laptop; time it. Watch Gemini latency on 3.5-flash-lite.
3. Record a backup video; Devpost write-up and the 2-3 minute video script.
4. Optional: tell Kai (mkflan) that master moved.

## Open questions / decisions waiting
- Keep "HackTX 2026" in the footer, or only the team credit?
- Should "Post as" for discussions also show the major (it does now, read-only)?

## Files touched
- frontend/templates/base.html: nav, accessibility popover, footer, text-size slider
- frontend/templates/{index,forum,post,project,chat,dashboard}.html: copy, forms, layout
- backend/pages.py, backend/forum.py: session user for posts and comments; all users in nav
- backend/json_api/config.py, env.example.txt: model defaults
- backend/tests/test_{pages,forum,gemini_provider,search}.py: new and updated tests
- README.md, docs/SPEC.md, docs/DEMO.md, docs/TODO.md: names, models, costs, run sheet

## How to run / test right now
- `cd backend` then `..\.venv\Scripts\python app.py` -> http://127.0.0.1:8000 (`/health` must say
  llm_model gemini-3.5-flash-lite, search_enabled true)
- `.venv\Scripts\python -m pytest` and `.venv\Scripts\ruff check backend scripts` (repo root)

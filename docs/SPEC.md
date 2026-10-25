# Research Rabbit: demo spec (HackTX 26)

Written 2026-10-24 late evening. The plan for the judged demo. Status lives in TODO.md; things
cut from the demo live in BACKLOG.md.

## Problem and user

Undergraduates want a project that fits their major, interests, time and skill, and that they
can put on a resume. Finding one, then finding trustworthy materials, docs, tutorials and papers
for it, is the slow part. Research Rabbit recommends projects, hands over real resources, and
gives a mentor chatbot that knows the project.

## The 60-second journey (what the video and the live demo show)

1. Landing page. A first-visit pop-up asks: username, major, interests, timeframe, difficulty.
   "Seal your profile" creates the user and opens their dashboard.
2. Dashboard (Netflix layout). Top row: "Recommended for you". Below: rows by major, by
   interest, by difficulty and by timeframe. Each card shows name, majors, interests,
   difficulty, timeframe.
3. Click a project: full page with description, tags, "Getting started" outline, materials and
   where to buy them (prices and stores from SerpApi Google Shopping), documentation, YouTube
   tutorials and papers (from SerpApi), and two buttons: "Ask the Caterpillar about this
   project" and "Make it mine" (Gemini personalizes the plan to this student).
4. Chatbot, project mode: Gemini answers with the project and its resources in context. A "Dig
   deeper" toggle runs a live SerpApi search and shows the result cards under the answer.
5. Chatbot, general mode: pitch an idea, develop it in conversation, press "Turn into a project
   starter": SerpApi finds real tutorials and papers for the idea, Gemini writes the full
   starter (milestones, materials, schedule), and "Post to Wonderland" publishes it.
6. Forum (Wonderland): community project starters, searchable and sortable, each rendered like
   a project page, with comments.
7. Switch to the second test user: the dashboard and recommendations change.

## Two test users (seeded)

| | alex_demo | maya_demo |
|---|---|---|
| major | Electrical and Computer Engineering | Computer Science |
| interests | sensors, plants, sustainability | language learning, web apps, data visualization |
| timeframe | 12 total hours (a weekend or two) | 40 total hours (about a month) |
| difficulty | beginner | intermediate |

Plus 6-8 fictional community members (other majors) who author the seeded forum starters.
The landing pop-up creates a third, live, during the demo.

## Pages and routes (Flask, `backend/app.py`)

| Route | Page |
|---|---|
| `GET /` | Landing. Pop-up profile form (shown automatically when no `user_id` cookie). |
| `POST /users` | Create the user from the form; set the cookie; redirect to the dashboard. |
| `POST /session/<user_id>` | Switch the current user (demo switcher in the nav). |
| `GET /dashboard` (and `/dashboard/<id>`) | Netflix rows. |
| `GET /projects/<id>` | Project page with grouped resources and the two buttons. |
| `GET /chat`, `GET /chat?project=<id>` | Chatbot page (general or project mode). |
| `GET /forum`, `POST /forum/posts`, `POST /forum/posts/<id>/comments` | Wonderland (exists; gains search, sort and starters). |
| `GET /forum/posts/<id>` | One starter rendered in full. |

Nav tabs (keeping the Wonderland language): Home, The Rabbit Hole (dashboard), Ask the
Caterpillar (chatbot), Wonderland (forum). Dark panel style, gold `#d4af37` accents, Cinzel and
Space Grotesk fonts, sky/grass/dirt sections stay as they are.

## JSON API additions (`backend/json_api`)

- `POST /api/users/<id>/assistant` body `{project_id?, messages:[{role, content}], dig_deeper?}`
  returns `{reply, sources:[Resource], web_results?, generation_mode}`. Stateless: the browser
  keeps the conversation. URLs in the reply that are not in the supplied sources are removed.
- `POST /api/users/<id>/starter` body `{idea, conversation?}` returns a `ProjectPlan` built with
  `elaborate_idea`, with a resource bank enriched by SerpApi for the idea.
- `RecommendationsRequest.limit` cap raised from 3 to 12 for the dashboard row.
- `NormalizedUser.skill_level` (optional) and ranking uses it when the request has none.

## LLM (Gemini)

- Default model `gemini-3.6-flash` (3.8 timed out or returned 503 on every live call today).
- New provider method `chat(system, turns) -> str` (plain text, no schema), plus the mock.
- New prompts: `assistant_project.md` (mentor for one catalog project: only cite supplied
  resources, give next steps, debug with the student) and `assistant_general.md` (develop a
  pitch into a scoped project; ask one question at a time; propose the starter when ready).
- Rule kept: the model never invents a URL or citation. Chat replies are checked.

## SerpApi (the sponsor track)

Role: Research Rabbit does not make up sources; it digs them up. `backend/serp.py` wraps
`https://serpapi.com/search.json` with httpx, with a `serp_cache` table keyed by engine+query so
nothing is searched twice and the demo works offline once warmed.

| Use | Engine | Stored as |
|---|---|---|
| Tutorials per project | `youtube` | resources, kind `tutorial`, provider `YouTube` |
| Papers per project | `google_scholar` | resources, kind `research`, metadata authors/year |
| Documentation per project | `google` | resources, kind `documentation` |
| Where to buy each material | `google_shopping` | `materials.shop_url`, `shop_source`, `price_usd` |
| "Dig deeper" in chat and on the project page | `youtube` + `google` | shown live, cached, fed to Gemini |
| Starter from a pitch | `youtube` + `google_scholar` | the starter's resource bank |

`scripts/enrich_catalog.py --max-searches N` fills the catalog in priority order (the two test
users' recommended projects first) and resumes from the cache. Everything SerpApi returns stays
`provided_unverified` (a search hit is not a content check) and is labeled with its provider.
Setting: `SERPAPI_API_KEY` in `env.txt`. Without it, the catalog still works from the authored
seed and the UI says "web search unavailable".

## Data (SQLite, schema v4)

- `users` + `difficulty` (beginner/intermediate/advanced, nullable).
- `projects` + `getting_started` (outline text), `timeframe_label`.
- `materials` (project_id, name, quantity, purpose, est_cost_usd, shop_url, shop_source,
  price_usd, fetched_at).
- `resources` + `fetched_at`, `source` (`authored` | `serpapi:<engine>`), `thumbnail_url`,
  `metadata` JSON.
- `posts` + `kind` (`discussion` | `starter`), `majors`, `interests`, `difficulty`,
  `estimated_hours`, `starter_json`.
- `serp_cache` (engine, query, fetched_at, json).
- Seed moves from `seed.sql` to `backend/catalog_data.py` (authored projects, materials,
  getting-started outlines, community users and starters) + `backend/seeding.py`.

Catalog target: about 45 projects across 9 majors (CS, ECE, Mechanical, Biomedical, Biology,
Chemistry/Biochem, Math/Statistics, Physics, Environmental), 5 per major, covering all three
difficulties and four timeframes (weekend <= 12 h, two weeks ~ 25 h, a month ~ 40 h, a semester
80+ h) and a shared vocabulary of about 30 interests (the landing checkboxes).

## Build order (each step leaves a working demo)

1. Schema v4, Python seeding with the full catalog, users with difficulty, landing form write
   path, cookie session, nav tabs and user switcher.
2. Dashboard rows and the project page (authored resources, "Make it mine").
3. Chat: provider method, prompts, endpoint, page, project and general modes, starter flow,
   post to forum.
4. SerpApi client, cache, enrichment script, live dig-deeper, starter enrichment.
5. Forum: starters, search, sort, community seed.
6. Tests for every write path and the mock chat; README, DEMO.md run sheet; final smoke run.

## Out of scope for the demo (see BACKLOG.md)

Login and passwords, editing a profile, saving chat history, verified resources, deployment to
a public URL (local demo unless decided otherwise), mobile polish.

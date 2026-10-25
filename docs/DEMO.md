# Demo run sheet (HackTX 26, local laptop)

## Before the judges arrive (10 minutes)

1. Check `.env` (or `env.txt`) in the repo root has `GEMINI_API_KEY`, `SERPAPI_API_KEY`,
   `LLM_MODE=gemini`, `GEMINI_MODEL=gemini-3.6-flash`. Never show this file on screen.
2. Start the app from a terminal in `backend/`:
   `..\.venv\Scripts\python app.py` then open http://127.0.0.1:8000 in a clean browser window
   (no cookies: use a private window, or click "New profile" in the nav).
3. Open `/health` once: `llm_mode: gemini`, `search_enabled: true`, `data_source: sqlite`.
4. Do NOT delete `backend/app.db`: it holds the SerpApi results already dug up for the catalog.
   If it is ever lost, restarting the app rebuilds everything from `backend/serp_cache.json`
   at zero cost; only "Dig deeper" on a project that was never enriched spends a search.
5. SerpApi free plan: 250 searches a month. Each "Dig deeper" costs 2, each starter 2, and
   repeats are free (cached). Check the balance at https://serpapi.com/dashboard.
6. Gemini calls take 5-20 s. Say what is happening while it thinks ("Gemini is writing a plan
   that fits twelve hours and a beginner").

## The 3-minute journey

| Step | Do | Say |
|---|---|---|
| 1 | Landing page. The profile pop-up opens. Type a username, pick **Physics**, tick **optics** and **astronomy**, choose **A month**, **intermediate**. Seal. | "Thirty seconds, no password. Major, interests, time, difficulty." |
| 2 | The Rabbit Hole. Point at the top shelf, then scroll: by major, by interest, by difficulty, by timeframe. | "The top shelf is ranked for this student. Nothing harder than intermediate, nothing over forty hours. Below, every project on campus, Netflix style." |
| 3 | Open **DIY Spectroscope for Lamp and Star Spectra**. Scroll the outline, the materials table with store links and prices, documentation, YouTube tutorials, papers. | "Every project ships with a getting-started outline, a shopping list with where to buy it, and sources. None of these links were typed by us or made up by a model: SerpApi dug them up, and each one says so." |
| 4 | Press **Dig deeper**. New cards appear. | "Live SerpApi: YouTube and web, cached so we never pay twice." |
| 5 | Press **Ask the Caterpillar about this project**. Ask: *"My spectrum lines are blurry, what should I fix first?"* Tick **Dig deeper**. | "Gemini knows this project's outline, materials and sources. It can only link to sources it was given; anything else is removed before the student sees it." |
| 6 | Nav: **Ask the Caterpillar** (general). Type: *"A phone app that reminds me to water my plants based on the weather."* Reply once, then press **Turn into a project starter**. | "Pitch an idea. SerpApi finds real tutorials and papers for it, Gemini writes the full starter: milestones, materials, schedule, sources." |
| 7 | Press **Post to Wonderland**. Show the starter page, then **Wonderland**: search "sensors", sort by fewest hours. | "Starters live in the community forum, searchable and sortable like the catalog." |
| 8 | Nav switcher: become **alex_demo**, open The Rabbit Hole. Then **maya_demo**. | "Alex: ECE, beginner, twelve hours: soil sensors and bike lights. Maya: CS, intermediate, a month: language apps and dashboards. Same catalog, different shelves." |

## If something fails

- Gemini 503 "high demand" or a timeout: the app already retries once on
  `GEMINI_FALLBACK_MODEL` (gemini-2.5-flash) and the reply footer shows which model answered.
  If both fail, say "the model is busy" and retry; the project page, shelves and forum never
  depend on Gemini. If it keeps failing, change `GEMINI_MODEL` in `.env` and restart.
- SerpApi quota gone: everything already dug up still shows; "Dig deeper" reports the failure
  honestly and the chat answers from supplied sources.
- Offline entirely: `LLM_MODE=mock` in `.env` gives deterministic mentor replies labeled "mock";
  the catalog and forum work unchanged.

## Two scripted users

| | alex_demo (id 1) | maya_demo (id 2) |
|---|---|---|
| major | Electrical and Computer Engineering | Computer Science |
| interests | sensors, plants, sustainability | language learning, web apps, data visualization |
| time | 12 total hours | 40 total hours |
| difficulty | beginner | intermediate |
| top shelf | Smart Soil Moisture Monitor, Bike Light with Automatic Brake Flash, ... | Language Learning Progress Dashboard, Phrasebook Chat Helper, ... |

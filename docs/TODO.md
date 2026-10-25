# TODO

What is finished and what still needs doing. Tick items as they land.

Owners: **Back** = backend (Rashmi and Viraj), **Front** = pages and templates, **Team** = anyone.

## Done (2026-10-24 and 25)

- [x] json_api: catalog, explainable ranking, time-fit rules, Gemini structured plans with one
      correction, resource grounding (only supplied IDs), error envelope, cache
- [x] SQLite schema v4, authored catalog of 47 projects across 9 majors (outlines, materials,
      guides), 10 users, idempotent Python seeding
- [x] Landing pop-up creates or re-enters a profile; cookie session; nav switcher
- [x] Netflix dashboard (recommended, by major, interest, difficulty, timeframe); project pages
- [x] The Caterpillar: Gemini chat in project and general mode, URL discipline, mock offline
- [x] SerpApi: injectable SearchProvider, cached client, "Dig deeper", starter sources,
      budgeted enrichment script, committed cache snapshot replayed on first start
- [x] Wonderland: starters with tags, search and sort, single-post pages, eight seeded starters
- [x] Tests on in-memory SQLite with the mock LLM and fake search; ruff clean
- [x] Live checks 2026-10-25 on gemini-3.6-flash: mentor reply with 6 SerpApi results in
      project mode; starter plan in 18 s
- [x] README, SPEC, DEMO run sheet, BACKLOG
- [x] Readability pass 2026-10-25: Space Grotesk headings (Cinzel only on the Home banner),
      lighter brown backdrop, green accents, matte (no shadows or blur), white clouds,
      larger text, A / A+ / A++ text size switch, shelf scrollbar and mouse-wheel scrolling

## Before judging

- [ ] **Team** Rehearse docs/DEMO.md twice end to end on the demo laptop; time it
- [ ] **Team** Record a backup video of the journey (in case Wi-Fi or quotas fail)
- [ ] **Team** Check SerpApi searches left at https://serpapi.com/dashboard (budget ~80 for
      rehearsal and the demo; each dig or starter costs 2)
- [ ] **Team** Devpost write-up and the 2-3 minute video script (see hackathon playbook)

## Later (see BACKLOG.md)

- [ ] Login and profile editing; saved chat history; verified sources; public deployment

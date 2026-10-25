-- Schema version 4. db.py refuses to start on an app.db made by an older version.
-- List columns (interests, majors, topic_tags) are comma-separated text; sqlite_provider.py
-- splits them. Time columns follow json_api's TimeValue: total_hours, hours_per_week and weeks
-- are different units and are never converted into each other.
-- v4: users.difficulty, projects.slug/getting_started, materials, resource provenance,
--     forum starters, serp_cache. Rows are seeded by seeding.py (not SQL).

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    major TEXT NOT NULL,
    interests TEXT NOT NULL, -- Comma separated list of the user's interests
    time_amount REAL CHECK (time_amount IS NULL OR time_amount >= 0),
    time_unit TEXT NOT NULL DEFAULT 'unknown'
        CHECK (time_unit IN ('total_hours', 'hours_per_week', 'weeks', 'unknown')),
    time_raw TEXT, -- What the student typed, e.g. '12 total hours'
    difficulty TEXT
        CHECK (difficulty IS NULL OR difficulty IN ('beginner', 'intermediate', 'advanced')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE, -- Stable handle used by the seed (e.g. 'soil-moisture-monitor')
    name TEXT NOT NULL UNIQUE,
    scope TEXT, -- Short description shown to students; NULL is fine
    majors TEXT NOT NULL DEFAULT '', -- Comma separated
    interests TEXT NOT NULL DEFAULT '', -- Comma separated
    timeline_amount REAL CHECK (timeline_amount IS NULL OR timeline_amount >= 0),
    timeline_unit TEXT NOT NULL DEFAULT 'unknown'
        CHECK (timeline_unit IN ('total_hours', 'hours_per_week', 'weeks', 'unknown')),
    timeline_raw TEXT,
    -- Only when the source states the workload; total_hours fills it automatically.
    timeline_estimated_hours REAL,
    difficulty TEXT
        CHECK (difficulty IS NULL OR difficulty IN ('beginner', 'intermediate', 'advanced')),
    getting_started TEXT -- Numbered outline, one step per line
);

-- Things to buy or gather. shop_* are filled from a real search result (SerpApi Google
-- Shopping) by scripts/enrich_catalog.py; NULL means "not looked up", never a guess.
CREATE TABLE IF NOT EXISTS materials (
    project_id INTEGER NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    name TEXT NOT NULL,
    quantity TEXT,
    purpose TEXT,
    estimated_cost_usd REAL CHECK (estimated_cost_usd IS NULL OR estimated_cost_usd >= 0),
    shop_url TEXT,
    shop_source TEXT,
    price_usd REAL CHECK (price_usd IS NULL OR price_usd >= 0),
    fetched_at TEXT,
    PRIMARY KEY (project_id, position)
);

-- A link (url) or a text guide (url NULL, content_excerpt set). Never invent URLs: a link is
-- either written by the team ('authored') or returned by a search engine ('serpapi:<engine>').
CREATE TABLE IF NOT EXISTS resources (
    project_id INTEGER NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    slug TEXT NOT NULL, -- Stable per project; the API ID is '<project_id>/<slug>'
    title TEXT NOT NULL,
    url TEXT,
    kind TEXT NOT NULL DEFAULT 'other'
        CHECK (kind IN ('guide', 'research', 'tutorial', 'documentation', 'example', 'other')),
    provider TEXT,
    topic_tags TEXT NOT NULL DEFAULT '', -- Comma separated
    content_excerpt TEXT,
    source TEXT NOT NULL DEFAULT 'authored',
    thumbnail_url TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}', -- authors, year, channel, ... as a JSON object
    fetched_at TEXT,
    PRIMARY KEY (project_id, slug)
);

-- Forum. Posts and comments belong to a user; a post may point at a project. A 'starter' post
-- carries a generated project plan (starter_json) plus tags so the forum can be searched and
-- sorted like the catalog. There is no login: the page lets the demo user pick who they are.
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects (id) ON DELETE SET NULL,
    kind TEXT NOT NULL DEFAULT 'discussion' CHECK (kind IN ('discussion', 'starter')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    majors TEXT NOT NULL DEFAULT '', -- Comma separated
    interests TEXT NOT NULL DEFAULT '', -- Comma separated
    difficulty TEXT
        CHECK (difficulty IS NULL OR difficulty IN ('beginner', 'intermediate', 'advanced')),
    estimated_hours REAL CHECK (estimated_hours IS NULL OR estimated_hours >= 0),
    starter_json TEXT, -- ProjectPlan JSON for kind = 'starter'
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES posts (id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_posts_created ON posts (created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments (post_id, id);

-- Every SerpApi response, keyed by engine + query, so a query is never paid for twice and the
-- demo works offline once warmed.
CREATE TABLE IF NOT EXISTS serp_cache (
    engine TEXT NOT NULL,
    query TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response_json TEXT NOT NULL,
    PRIMARY KEY (engine, query)
);

PRAGMA user_version = 4;

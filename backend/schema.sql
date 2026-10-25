-- Schema version 2. db.py refuses to start on an app.db made by an older version.
-- List columns (interests, majors, topic_tags) are comma-separated text; sqlite_provider.py
-- splits them. Time columns follow json_api's TimeValue: total_hours, hours_per_week and weeks
-- are different units and are never converted into each other.

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    major TEXT NOT NULL,
    interests TEXT NOT NULL, -- Comma separated list of the user's interests
    time_amount REAL CHECK (time_amount IS NULL OR time_amount >= 0),
    time_unit TEXT NOT NULL DEFAULT 'unknown'
        CHECK (time_unit IN ('total_hours', 'hours_per_week', 'weeks', 'unknown')),
    time_raw TEXT -- What the student typed, e.g. '12 total hours'
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        CHECK (difficulty IS NULL OR difficulty IN ('beginner', 'intermediate', 'advanced'))
);

-- A link (url) or a text guide (url NULL, content_excerpt set). Never invent URLs.
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
    PRIMARY KEY (project_id, slug)
);

PRAGMA user_version = 2;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    major TEXT NOT NULL,
    interests TEXT NOT NULL -- Comma separated list of the user's intersts
);

CREATE TABLE IF NOT EXISTS projects (
    name TEXT PRIMARY KEY,
    scope TEXT NOT NULL UNIQUE
);
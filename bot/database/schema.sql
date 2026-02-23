CREATE TABLE IF NOT EXISTS games (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT,
    added_by_id INTEGER NOT NULL,
    added_by_username TEXT,
    added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active   BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS polls (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_poll_id  TEXT NOT NULL UNIQUE,
    message_id        INTEGER,
    chat_id           INTEGER NOT NULL,
    poll_type         TEXT NOT NULL,
    options_map       TEXT NOT NULL,
    related_game_id   INTEGER REFERENCES games(id),
    is_closed         BOOLEAN DEFAULT 0,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS poll_votes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_poll_id TEXT NOT NULL,
    user_id          INTEGER NOT NULL,
    full_name        TEXT,
    username         TEXT,
    option_ids       TEXT NOT NULL,
    voted_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ratings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id    INTEGER NOT NULL REFERENCES games(id),
    poll_id    INTEGER REFERENCES polls(id),
    user_id    INTEGER NOT NULL,
    full_name  TEXT,
    username   TEXT,
    score      INTEGER NOT NULL CHECK(score BETWEEN 1 AND 10),
    rated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

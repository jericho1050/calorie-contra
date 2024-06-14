CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    hash TEXT NOT NULL
);

CREATE TABLE food_count (
    user_id INTEGER NOT NULL,
    food_name TEXT NOT NULL,
    calories NUMERIC,
    protein NUMERIC,
    carbs NUMERIC,
    fat NUMERIC,
    month INTEGER,
    day INTEGER,
    year INTEGER,
    hour INTEGER,
    minute INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
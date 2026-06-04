CREATE TABLE Athlete (
    id INTEGER PRIMARY KEY,
    name TEXT,
    gender TEXT,
    age INTEGER
);

CREATE TABLE Gear (
    gear_id INTEGER PRIMARY KEY,
    name TEXT,
    brand TEXT,
    distance_used NUMERIC(6,2),
    max_km NUMERIC(7,0)
);

CREATE TABLE Activity (
    activity_id BIGINT PRIMARY KEY,
    athlete_id  INTEGER REFERENCES Athlete(id),
    gear_id     INTEGER REFERENCES Gear(gear_id),
    type        TEXT,
    date        DATE,
    title       TEXT,
    distance_km NUMERIC(6,2),
    duration_min NUMERIC(6,2),
    elevation_m NUMERIC(6,2),
    avg_pace    TEXT,
    calories    INTEGER,
    avg_hr_bpm  INTEGER
);

CREATE TABLE Route (
    name       TEXT,
    route_id   TEXT PRIMARY KEY,
    activity_id INTEGER REFERENCES Activity(activity_id)
);

CREATE TABLE Segments (
    segment_id  TEXT PRIMARY KEY,
    activity_id INTEGER REFERENCES Activity(activity_id),
    length      NUMERIC(6,2)
);

-- View: alle løbeture med beregnet pace (bonus)
CREATE VIEW running_stats AS
SELECT
    date,
    title,
    distance_km,
    duration_min,
    ROUND((duration_min / NULLIF(distance_km, 0))::NUMERIC, 2) AS pace_min_km,
    elevation_m,
    avg_hr_bpm,
    calories
FROM Activity
WHERE type = 'Run' AND distance_km > 0;


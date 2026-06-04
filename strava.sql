<<<<<<< HEAD
CREATE TABLE IF NOT EXISTS Athlete (
=======
CREATE TABLE Athlete (
>>>>>>> 9adb4cf46f243019b2c3608690b42fcc786e8487
    id INTEGER PRIMARY KEY,
    name TEXT,
    gender TEXT,
    age INTEGER
);

<<<<<<< HEAD
CREATE TABLE IF NOT EXISTS Gear (
=======
CREATE TABLE Gear (
>>>>>>> 9adb4cf46f243019b2c3608690b42fcc786e8487
    gear_id INTEGER PRIMARY KEY,
    name TEXT,
    brand TEXT,
    distance_used NUMERIC(6,2),
    max_km NUMERIC(7,0)
);

<<<<<<< HEAD
CREATE TABLE IF NOT EXISTS Activity (
=======
CREATE TABLE Activity (
>>>>>>> 9adb4cf46f243019b2c3608690b42fcc786e8487
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

<<<<<<< HEAD
CREATE TABLE IF NOT EXISTS Route (
    name        TEXT,
    route_id    TEXT PRIMARY KEY,
    activity_id INTEGER REFERENCES Activity(activity_id)
);

CREATE TABLE IF NOT EXISTS Segments (
=======
CREATE TABLE Route (
    name       TEXT,
    route_id   TEXT PRIMARY KEY,
    activity_id INTEGER REFERENCES Activity(activity_id)
);

CREATE TABLE Segments (
>>>>>>> 9adb4cf46f243019b2c3608690b42fcc786e8487
    segment_id  TEXT PRIMARY KEY,
    activity_id INTEGER REFERENCES Activity(activity_id),
    length      NUMERIC(6,2)
);

-- View: alle løbeture med beregnet pace (bonus)
<<<<<<< HEAD
CREATE OR REPLACE VIEW running_stats AS
=======
CREATE VIEW running_stats AS
>>>>>>> 9adb4cf46f243019b2c3608690b42fcc786e8487
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
<<<<<<< HEAD
=======

>>>>>>> 9adb4cf46f243019b2c3608690b42fcc786e8487

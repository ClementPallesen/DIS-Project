-- Gennemsnit per aktivitetstype
SELECT type,
    ROUND(AVG(distance_km)::NUMERIC,  2) AS gns_distance_km,
    ROUND(AVG(duration_min)::NUMERIC, 2) AS gns_duration_min,
    ROUND(AVG(avg_hr_bpm)::NUMERIC,   2) AS gns_HR,
    ROUND(AVG(calories)::NUMERIC,     2) AS gns_calories,
    ROUND(AVG(elevation_m)::NUMERIC,  2) AS gns_elevation
FROM Activity
GROUP BY type
ORDER BY type;

-- Maksimum per aktivitetstype
SELECT type,
    ROUND(MAX(distance_km)::NUMERIC,  2) AS max_distance,
    ROUND(MAX(duration_min)::NUMERIC, 2) AS max_duration,
    ROUND(MAX(avg_hr_bpm)::NUMERIC,   2) AS max_HR,
    ROUND(MAX(calories)::NUMERIC,     2) AS max_calories,
    ROUND(MAX(elevation_m)::NUMERIC,  2) AS max_elevation
FROM Activity
GROUP BY type
ORDER BY type;

-- Minimum per aktivitetstype
SELECT type,
    ROUND(MIN(distance_km)::NUMERIC,  2) AS min_distance,
    ROUND(MIN(duration_min)::NUMERIC, 2) AS min_duration,
    ROUND(MIN(avg_hr_bpm)::NUMERIC,   2) AS min_hr,
    ROUND(MIN(calories)::NUMERIC,     2) AS min_calories,
    ROUND(MIN(elevation_m)::NUMERIC,  2) AS min_elevation
FROM Activity
GROUP BY type
ORDER BY type;

-- Løbeture over 10 km med pace
SELECT date, title, distance_km,
    duration_min,
    ROUND((duration_min / distance_km)::NUMERIC, 2) AS pace_min_km
FROM Activity
WHERE type = 'Run' AND distance_km >= 10
ORDER BY distance_km DESC;

-- Cykelture over 10 km
SELECT date, title, distance_km, duration_min
FROM Activity
WHERE type = 'Ride' AND distance_km >= 10
ORDER BY distance_km DESC;

-- Regex-match: aktiviteter med "Morning" i titel (PostgreSQL ~ operator)
SELECT date, type, title, distance_km
FROM Activity
WHERE title ~ 'Morning'
ORDER BY date DESC;

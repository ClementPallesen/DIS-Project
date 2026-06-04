"""
Import Strava activities CSV into the database.

To get your CSV:
  Strava → Settings → My Account → Download or Delete Your Account
  → Request Your Archive → download ZIP → find activities.csv

Usage:
  python import.py                        # default: activities.csv
  python import.py my_export.csv          # custom file
  python import.py activities.csv "Anna"  # custom name
"""

import csv
import sys
import psycopg2
from datetime import datetime

CSV_FILE     = sys.argv[1] if len(sys.argv) > 1 else "activities.csv"
ATHLETE_NAME = sys.argv[2] if len(sys.argv) > 2 else "Clement"

conn = psycopg2.connect(
    dbname="strava",
    user="postgres",
    password="",
    host="localhost"
)
cur = conn.cursor()

# Clear existing data so re-imports stay clean
cur.execute("DELETE FROM Activity")
cur.execute("DELETE FROM Gear")
cur.execute("DELETE FROM Athlete")

cur.execute("""
    INSERT INTO Athlete (id, name, gender, age)
    VALUES (1, %s, NULL, NULL)
    ON CONFLICT (id) DO NOTHING;
""", (ATHLETE_NAME,))

gear_map = {}

with open(CSV_FILE, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        gear_name = row.get("Activity Gear", "").strip()
        if gear_name and gear_name not in gear_map:
            gear_map[gear_name] = len(gear_map) + 1

for gear_name, gear_id in gear_map.items():
    cur.execute("""
        INSERT INTO Gear (gear_id, name, brand, distance_used, max_km)
        VALUES (%s, %s, NULL, 0, NULL)
        ON CONFLICT (gear_id) DO NOTHING;
    """, (gear_id, gear_name))

with open(CSV_FILE, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    inserted = 0
    skipped  = 0

    for row in reader:
        try:
            activity_id   = int(row["Activity ID"])
            date          = datetime.strptime(row["Activity Date"].strip(), "%b %d, %Y, %I:%M:%S %p").date()
            activity_type = row["Activity Type"].strip() or None
            title         = row["Activity Name"].strip() or None

            raw_dist      = row["Distance"].replace(",", "").strip()
            distance_km   = round(float(raw_dist) / 1000, 2) if raw_dist else None

            elapsed       = row["Elapsed Time"].strip()
            duration_min  = round(float(elapsed) / 60, 2) if elapsed else None

            elev          = row["Elevation Gain"].strip()
            elevation_m   = float(elev) if elev else None

            hr            = row["Average Heart Rate"].strip()
            avg_hr        = int(float(hr)) if hr else None

            cal           = row["Calories"].strip()
            calories      = int(float(cal)) if cal else None

            gear_name     = row.get("Activity Gear", "").strip()
            gear_id       = gear_map.get(gear_name) if gear_name else None

            cur.execute("""
                INSERT INTO Activity (
                    activity_id, athlete_id, gear_id, type, date, title,
                    distance_km, duration_min, elevation_m, avg_pace,
                    calories, avg_hr_bpm
                )
                VALUES (%s, 1, %s, %s, %s, %s, %s, %s, %s, NULL, %s, %s)
                ON CONFLICT (activity_id) DO NOTHING;
            """, (
                activity_id, gear_id, activity_type, date, title,
                distance_km, duration_min, elevation_m,
                calories, avg_hr
            ))
            inserted += 1

        except Exception as e:
            conn.rollback()
            print(f"Fejl på række {row.get('Activity ID', '?')}: {e}")
            skipped += 1

conn.commit()
cur.close()
conn.close()

print(f"Færdig! {inserted} aktiviteter indsat ({skipped} sprunget over) for '{ATHLETE_NAME}'.")
print("Husk at sætte gear-levetid (max_km) på Gear-siden i appen.")

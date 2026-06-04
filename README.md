# DIS-Project: Strava Activity Database

A Flask web application for exploring personal Strava training data stored in a PostgreSQL database.

---

## E/R Diagram

See `ER Diagram.pdf` in the repository root.

**Entities:** Athlete, Activity, Gear, Route, Segments  
**Relationships:**
- An Athlete *performs* many Activities
- An Activity *uses* a Gear (optional)
- An Activity *has* a Route (optional)
- A Route *has* Segments

---

## Database Schema

Defined in `strava.sql`. Tables:

| Table      | Key columns |
|------------|-------------|
| `Athlete`  | id, name, gender, age |
| `Gear`     | gear_id, name, brand, distance_used |
| `Activity` | activity_id, type, date, title, distance_km, duration_min, elevation_m, avg_hr_bpm, calories |
| `Route`    | route_id, name, activity_id |
| `Segments` | segment_id, activity_id, length |

**Bonus – database view:** `running_stats` aggregates all running activities with computed pace (min/km).

---

## Setup: Initialize the Database

### Prerequisites
- PostgreSQL 14+
- Python 3.10+

### 1. Install Python dependencies

```bash
pip install flask psycopg2-binary
```

### 2. Create the PostgreSQL database

```bash
createdb strava
psql -d strava -f strava.sql
```

### 3. Import Strava data from CSV

```bash
python import.py
```

This reads `activities.csv` (exported from Strava) and inserts all activities into the database.

---

## Running the Web App

```bash
python Strava.py
```

Open your browser at **http://localhost:5000**

---

## Features & Interaction

| Page | URL | SQL operations |
|------|-----|----------------|
| Dashboard | `/` | `SELECT AVG/SUM/COUNT … GROUP BY type` |
| Activities | `/activities` | `SELECT … LEFT JOIN … WHERE` with optional filters |
| Search | `/search` | `SELECT … WHERE title ~ <regex>` |
| Gear | `/gear` | `SELECT … GROUP BY` + `UPDATE Gear SET max_km` |
| Statistics | `/stats` | `SELECT` + `running_stats` view |
| Add activity | `/add` | `INSERT INTO Activity` |
| Delete activity | (button on Activities) | `DELETE FROM Activity WHERE activity_id = …` |

### Gear tracking
The **Gear** page (`/gear`) shows total km per shoe/bike with a colour-coded progress bar.
Click *Tilpas levetid* on any gear card to set your own km threshold — this runs an `UPDATE Gear SET max_km = …` statement.
Typical thresholds: running shoes 500–800 km, road bike 10 000–20 000 km.

### Filters
- Filter activities by **type** (Run, Ride, Swim, …)
- Filter by **minimum distance** (e.g. all runs over 10 km)

---

## Regular Expression Matching

The **Search** page (`/search`) performs regex matching on activity titles:

1. Python's `re.compile()` validates the pattern client-side and returns a user-friendly error for invalid patterns.
2. PostgreSQL's `~` operator executes the match in the database:
   ```sql
   SELECT ... FROM Activity WHERE title ~ '<pattern>'
   ```

Example patterns:
- `Morning` – finds all activities with "Morning" in the title
- `^Evening` – titles starting with "Evening"
- `Run|Ride` – titles containing "Run" or "Ride"
- `(?i)run` – case-insensitive match

---

## Bonus: Database View

`running_stats` is defined in `strava.sql` and used on the Statistics page:

```sql
CREATE VIEW running_stats AS
SELECT date, title, distance_km, duration_min,
    ROUND((duration_min / NULLIF(distance_km, 0))::NUMERIC, 2) AS pace_min_km,
    elevation_m, avg_hr_bpm, calories
FROM Activity
WHERE type = 'Run' AND distance_km > 0;
```

---

## Using Your Own Strava Data

Any Strava user can run this app with their own data:

1. Go to **Strava → Settings → My Account → Download or Delete Your Account → Request Your Archive**
2. Download the ZIP and extract `activities.csv`
3. Place it in the project folder
4. Re-initialise the database:
   ```bash
   psql -d strava -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
   psql -d strava -f strava.sql
   python import.py activities.csv "Your Name"
   ```
5. Run `python Strava.py` — the app works identically with any Strava export

The Strava CSV export format is the same for all accounts. Gear names are taken directly from your Strava gear entries. After import, visit `/gear` to set km thresholds for your equipment.

---

## AI Declaration

Parts of this project were developed with assistance from **Claude (Anthropic)**, an AI assistant, specifically for:
- Scaffolding the Flask web application structure
- Writing and fixing SQL queries
- HTML/CSS templates

All training data is personal data exported from the author's own Strava account. The database design, E/R model, and data import logic were developed by the author.

from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import psycopg2.extras
import re

app = Flask(__name__)
app.secret_key = 'strava-dis-2026'

DB_CONFIG = dict(dbname="strava", user="postgres", password="", host="localhost")


def get_db():
    return psycopg2.connect(**DB_CONFIG)


def fmt_pace(pace_min_km, activity_type=None):
    """Format pace/speed depending on activity type.

    Run/default : M:SS/km   (pace_min_km as-is)
    Ride        : X.X km/t  (60 / pace_min_km)
    Swim        : M:SS/100m (pace_min_km / 10)
    """
    if pace_min_km is None:
        return '—'
    p = float(pace_min_km)
    if p <= 0:
        return '—'

    t = (activity_type or '').lower()

    if t == 'ride':
        kmh = 60.0 / p
        return f"{kmh:.1f} km/t"

    if t == 'swim':
        p100 = p / 10.0
        mins = int(p100)
        secs = round((p100 - mins) * 60)
        return f"{mins}:{secs:02d}/100m"

    # Run or anything else
    mins = int(p)
    secs = round((p - mins) * 60)
    return f"{mins}:{secs:02d}/km"


app.jinja_env.globals['fmt_pace'] = fmt_pace


@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT type,
            COUNT(*)                                                         AS count,
            ROUND(SUM(distance_km)::NUMERIC, 1)                             AS total_km,
            ROUND(AVG(distance_km)::NUMERIC, 2)                             AS avg_km,
            ROUND(AVG(duration_min)::NUMERIC, 1)                            AS avg_min,
            ROUND(AVG(avg_hr_bpm)::NUMERIC, 0)                              AS avg_hr,
            ROUND(AVG(calories)::NUMERIC, 0)                                AS avg_cal,
            ROUND(AVG(CASE WHEN distance_km > 0
                          THEN duration_min / distance_km END)::NUMERIC, 2) AS avg_pace
        FROM Activity
        WHERE type IS NOT NULL
        GROUP BY type
        ORDER BY count DESC
    """)
    stats = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', stats=stats)


@app.route('/activities')
def activities():
    activity_type = request.args.get('type', '')
    min_distance = request.args.get('min_distance', '')

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = """
        SELECT a.activity_id, a.type, a.date, a.title,
               a.distance_km, a.duration_min, a.elevation_m,
               a.avg_hr_bpm, a.calories,
               g.name AS gear_name,
               CASE
                   WHEN a.distance_km > 0 AND a.duration_min > 0
                   THEN ROUND((a.duration_min / a.distance_km)::NUMERIC, 2)
                   ELSE NULL
               END AS pace_min_km
        FROM Activity a
        LEFT JOIN Gear g ON a.gear_id = g.gear_id
        WHERE 1=1
    """
    params = []

    if activity_type:
        query += " AND a.type = %s"
        params.append(activity_type)

    if min_distance:
        try:
            query += " AND a.distance_km >= %s"
            params.append(float(min_distance))
        except ValueError:
            pass

    query += " ORDER BY a.date DESC LIMIT 300"

    cur.execute(query, params)
    acts = cur.fetchall()

    cur.execute("SELECT DISTINCT type FROM Activity WHERE type IS NOT NULL ORDER BY type")
    types = [r['type'] for r in cur.fetchall()]

    cur.close()
    conn.close()
    return render_template('activities.html', activities=acts, types=types,
                           selected_type=activity_type, min_distance=min_distance)


@app.route('/search', methods=['GET', 'POST'])
def search():
    """Regex search on activity titles using Python re + PostgreSQL ~ operator."""
    results = []
    pattern = ''
    error = ''
    searched = False

    if request.method == 'POST':
        pattern = request.form.get('pattern', '').strip()
        searched = True
        if pattern:
            # Validate regex client-side first
            try:
                re.compile(pattern)
            except re.error as e:
                error = f"Ugyldigt regex-mønster: {e}"
                return render_template('search.html', results=results,
                                       pattern=pattern, error=error, searched=searched)

            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                # PostgreSQL ~ performs case-sensitive regex matching
                cur.execute("""
                    SELECT activity_id, type, date, title,
                           distance_km, duration_min,
                           CASE
                               WHEN distance_km > 0 AND duration_min > 0
                               THEN ROUND((duration_min / distance_km)::NUMERIC, 2)
                               ELSE NULL
                           END AS pace_min_km
                    FROM Activity
                    WHERE title ~ %s
                    ORDER BY date DESC
                """, (pattern,))
                results = cur.fetchall()
            except psycopg2.Error as e:
                error = f"Database-fejl ved regex: {e}"
            finally:
                cur.close()
                conn.close()

    return render_template('search.html', results=results, pattern=pattern,
                           error=error, searched=searched)


@app.route('/gear')
def gear():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT g.gear_id, g.name, g.brand, g.max_km,
               COUNT(a.activity_id)                      AS uses,
               ROUND(SUM(a.distance_km)::NUMERIC, 1)     AS total_km,
               MAX(a.date)                               AS last_used,
               STRING_AGG(DISTINCT a.type, ', '
                   ORDER BY a.type)                      AS activity_types
        FROM Gear g
        LEFT JOIN Activity a ON a.gear_id = g.gear_id
        GROUP BY g.gear_id, g.name, g.brand, g.max_km
        ORDER BY total_km DESC NULLS LAST
    """)
    gear_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('gear.html', gear_list=gear_list)


@app.route('/gear/<int:gear_id>/update', methods=['POST'])
def update_gear_threshold(gear_id):
    max_km = request.form.get('max_km', '').strip()
    if max_km:
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE Gear SET max_km = %s WHERE gear_id = %s",
                        (int(max_km), gear_id))
            conn.commit()
            flash('Grænseværdi opdateret.', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Fejl: {e}', 'error')
        finally:
            cur.close()
            conn.close()
    return redirect(url_for('gear'))


@app.route('/stats')
def stats():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT type,
            COUNT(*)                                                         AS count,
            ROUND(AVG(distance_km)::NUMERIC, 2)                             AS avg_distance,
            ROUND(MAX(distance_km)::NUMERIC, 2)                             AS max_distance,
            ROUND(MIN(distance_km)::NUMERIC, 2)                             AS min_distance,
            ROUND(AVG(duration_min)::NUMERIC, 1)                            AS avg_duration,
            ROUND(MAX(duration_min)::NUMERIC, 1)                            AS max_duration,
            ROUND(AVG(avg_hr_bpm)::NUMERIC, 0)                              AS avg_hr,
            ROUND(AVG(calories)::NUMERIC, 0)                                AS avg_cal,
            ROUND(SUM(elevation_m)::NUMERIC, 0)                             AS total_elev,
            ROUND(AVG(CASE WHEN distance_km > 0
                          THEN duration_min / distance_km END)::NUMERIC, 2) AS avg_pace
        FROM Activity
        WHERE type IS NOT NULL
        GROUP BY type
        ORDER BY type
    """)
    type_stats = cur.fetchall()

    # Use the running_stats view (bonus: database view)
    cur.execute("SELECT * FROM running_stats ORDER BY date DESC LIMIT 50")
    run_stats = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('stats.html', type_stats=type_stats, run_stats=run_stats)


@app.route('/add', methods=['GET', 'POST'])
def add_activity():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COALESCE(MAX(activity_id), 0) + 1 FROM Activity")
            new_id = cur.fetchone()[0]

            atype    = request.form.get('type') or None
            date     = request.form.get('date') or None
            title    = request.form.get('title', '').strip() or None
            distance = request.form.get('distance', '').strip()
            duration = request.form.get('duration', '').strip()
            elevation= request.form.get('elevation', '').strip()
            hr       = request.form.get('avg_hr', '').strip()
            calories = request.form.get('calories', '').strip()

            cur.execute("""
                INSERT INTO Activity (
                    activity_id, athlete_id, type, date, title,
                    distance_km, duration_min, elevation_m,
                    avg_hr_bpm, calories
                ) VALUES (%s, 1, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                new_id, atype, date, title,
                float(distance)  if distance  else None,
                float(duration)  if duration  else None,
                float(elevation) if elevation else None,
                int(hr)          if hr        else None,
                int(calories)    if calories  else None,
            ))
            conn.commit()
            flash('Aktivitet tilføjet!', 'success')
            return redirect(url_for('activities'))
        except Exception as e:
            conn.rollback()
            flash(f'Fejl ved indsætning: {e}', 'error')
        finally:
            cur.close()
            conn.close()

    return render_template('add_activity.html')


@app.route('/delete/<int:activity_id>', methods=['POST'])
def delete_activity(activity_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Activity WHERE activity_id = %s", (activity_id,))
        conn.commit()
        flash('Aktivitet slettet.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Fejl ved sletning: {e}', 'error')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('activities'))


if __name__ == '__main__':
    # Port 5000 is reserved by AirPlay on macOS; use 5001
    app.run(debug=True, port=5001)

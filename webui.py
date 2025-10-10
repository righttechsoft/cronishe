import os
import json
from bottle import Bottle, request, response, template, static_file, redirect, TEMPLATE_PATH
from datetime import datetime
from database import init_database, get_db
from zoneinfo import available_timezones

app = Bottle()

# Template directory
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
TEMPLATE_PATH.insert(0, TEMPLATE_DIR)


def get_schedule_text(job):
    """Convert job schedule to human-readable text"""
    if job['frequency_type'] == 'every':
        minutes = job['frequency_every_min']
        if minutes == 1:
            return "Every minute"
        elif minutes == 60:
            return "Every hour"
        elif minutes % 60 == 0:
            hours = minutes // 60
            return f"Every {hours} hour{'s' if hours > 1 else ''}"
        else:
            return f"Every {minutes} minutes"
    else:  # 'at'
        days = []
        day_names = {
            'frequency_at_mon': 'Mon',
            'frequency_at_tue': 'Tue',
            'frequency_at_wed': 'Wed',
            'frequency_at_thu': 'Thu',
            'frequency_at_fri': 'Fri',
            'frequency_at_sat': 'Sat',
            'frequency_at_sun': 'Sun'
        }
        for col, name in day_names.items():
            if job[col]:
                days.append(name)

        hr = job['frequency_at_hr'] if job['frequency_at_hr'] is not None else 0
        mn = job['frequency_at_min'] if job['frequency_at_min'] is not None else 0
        time_str = f"{hr:02d}:{mn:02d}"

        if days:
            return f"{', '.join(days)} at {time_str}"
        else:
            return f"At {time_str}"


def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS"""
    if seconds is None:
        return '-'

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_timezone_list():
    """Get list of timezones with priority zones first (UTC, NZ, AU, US)"""
    all_timezones = sorted(available_timezones())

    # Priority timezones
    priority_zones = []

    # Add UTC first
    if 'UTC' in all_timezones:
        priority_zones.append('UTC')

    # Add NZ timezones
    priority_zones.extend([tz for tz in all_timezones if tz.startswith('Pacific/') and 'Auckland' in tz or 'Chatham' in tz])

    # Add AU timezones
    priority_zones.extend([tz for tz in all_timezones if tz.startswith('Australia/')])

    # Add US timezones
    priority_zones.extend([tz for tz in all_timezones if tz.startswith('America/') and any(city in tz for city in ['New_York', 'Chicago', 'Denver', 'Los_Angeles', 'Phoenix', 'Anchorage', 'Honolulu'])])
    priority_zones.extend([tz for tz in all_timezones if tz.startswith('US/')])

    # Remove duplicates while preserving order
    seen = set()
    priority_zones = [tz for tz in priority_zones if tz not in seen and not seen.add(tz)]

    # Get remaining timezones
    remaining_zones = [tz for tz in all_timezones if tz not in priority_zones]

    return priority_zones + remaining_zones


@app.route('/')
def index():
    """Main page - list all jobs"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY id")
        jobs = [dict(row) for row in cursor.fetchall()]

        # Get last run duration for each job
        for job in jobs:
            cursor.execute("""
                SELECT duration FROM job_runs
                WHERE job_id = ?
                ORDER BY start_at DESC
                LIMIT 1
            """, (job['id'],))
            last_run = cursor.fetchone()
            job['last_duration'] = format_duration(last_run['duration']) if last_run and last_run['duration'] is not None else '-'

    # Enhance job data with formatted schedule
    for job in jobs:
        job['schedule_text'] = get_schedule_text(job)
        # Pass raw timestamp for client-side conversion
        if job['last_run']:
            job['last_run_utc'] = job['last_run']
        else:
            job['last_run_utc'] = None

    return template('index', jobs=jobs)


@app.route('/job/add')
def add_job_form():
    """Show add job form"""
    timezones = get_timezone_list()
    return template('add_job', timezones=timezones)


@app.route('/job/add', method='POST')
def add_job_submit():
    """Handle add job form submission"""
    name = request.forms.get('name')
    path = request.forms.get('path')
    frequency_type = request.forms.get('frequency_type')
    timezone = request.forms.get('timezone') or 'UTC'
    on_start = request.forms.get('on_start') or None
    on_success = request.forms.get('on_success') or None
    on_fail = request.forms.get('on_fail') or None

    with get_db() as conn:
        cursor = conn.cursor()

        if frequency_type == 'every':
            every_min = int(request.forms.get('frequency_every_min', 0))
            cursor.execute("""
                INSERT INTO jobs (name, path, frequency_type, frequency_every_min, timezone, active, on_start, on_success, on_fail)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
            """, (name, path, 'every', every_min, timezone, on_start, on_success, on_fail))
        else:  # 'at'
            mon = 1 if request.forms.get('day_mon') else 0
            tue = 1 if request.forms.get('day_tue') else 0
            wed = 1 if request.forms.get('day_wed') else 0
            thu = 1 if request.forms.get('day_thu') else 0
            fri = 1 if request.forms.get('day_fri') else 0
            sat = 1 if request.forms.get('day_sat') else 0
            sun = 1 if request.forms.get('day_sun') else 0
            hour = int(request.forms.get('frequency_at_hr', 0))
            minute = int(request.forms.get('frequency_at_min', 0))

            cursor.execute("""
                INSERT INTO jobs (name, path, frequency_type,
                    frequency_at_mon, frequency_at_tue, frequency_at_wed, frequency_at_thu,
                    frequency_at_fri, frequency_at_sat, frequency_at_sun,
                    frequency_at_hr, frequency_at_min, timezone, active, on_start, on_success, on_fail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """, (name, path, 'at', mon, tue, wed, thu, fri, sat, sun, hour, minute, timezone, on_start, on_success, on_fail))

        conn.commit()

    redirect('/')


@app.route('/job/<job_id:int>/edit')
def edit_job_form(job_id):
    """Show edit job form"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()

        if not job:
            redirect('/')

        job = dict(job)

    timezones = get_timezone_list()
    return template('edit_job', job=job, timezones=timezones)


@app.route('/job/<job_id:int>/edit', method='POST')
def edit_job_submit(job_id):
    """Handle edit job form submission"""
    name = request.forms.get('name')
    path = request.forms.get('path')
    frequency_type = request.forms.get('frequency_type')
    timezone = request.forms.get('timezone') or 'UTC'
    on_start = request.forms.get('on_start') or None
    on_success = request.forms.get('on_success') or None
    on_fail = request.forms.get('on_fail') or None

    with get_db() as conn:
        cursor = conn.cursor()

        if frequency_type == 'every':
            every_min = int(request.forms.get('frequency_every_min', 0))
            cursor.execute("""
                UPDATE jobs SET name=?, path=?, frequency_type=?, frequency_every_min=?,
                    frequency_at_mon=NULL, frequency_at_tue=NULL, frequency_at_wed=NULL,
                    frequency_at_thu=NULL, frequency_at_fri=NULL, frequency_at_sat=NULL,
                    frequency_at_sun=NULL, frequency_at_hr=NULL, frequency_at_min=NULL,
                    timezone=?, on_start=?, on_success=?, on_fail=?
                WHERE id=?
            """, (name, path, 'every', every_min, timezone, on_start, on_success, on_fail, job_id))
        else:  # 'at'
            mon = 1 if request.forms.get('day_mon') else 0
            tue = 1 if request.forms.get('day_tue') else 0
            wed = 1 if request.forms.get('day_wed') else 0
            thu = 1 if request.forms.get('day_thu') else 0
            fri = 1 if request.forms.get('day_fri') else 0
            sat = 1 if request.forms.get('day_sat') else 0
            sun = 1 if request.forms.get('day_sun') else 0
            hour = int(request.forms.get('frequency_at_hr', 0))
            minute = int(request.forms.get('frequency_at_min', 0))

            cursor.execute("""
                UPDATE jobs SET name=?, path=?, frequency_type=?,
                    frequency_every_min=NULL,
                    frequency_at_mon=?, frequency_at_tue=?, frequency_at_wed=?, frequency_at_thu=?,
                    frequency_at_fri=?, frequency_at_sat=?, frequency_at_sun=?,
                    frequency_at_hr=?, frequency_at_min=?, timezone=?, on_start=?, on_success=?, on_fail=?
                WHERE id=?
            """, (name, path, 'at', mon, tue, wed, thu, fri, sat, sun, hour, minute, timezone, on_start, on_success, on_fail, job_id))

        conn.commit()

    redirect('/')


@app.route('/job/<job_id:int>/toggle')
def toggle_job(job_id):
    """Toggle job active status"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE jobs SET active = 1 - active WHERE id = ?", (job_id,))
        conn.commit()

    redirect('/')


@app.route('/job/<job_id:int>/delete', method='POST')
def delete_job(job_id):
    """Delete a job"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()

    redirect('/')


@app.route('/job/<job_id:int>/runs')
def job_runs(job_id):
    """Show job run history"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get job details
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        if not job:
            redirect('/')
        job = dict(job)

        # Get runs
        cursor.execute("""
            SELECT * FROM job_runs
            WHERE job_id = ?
            ORDER BY start_at DESC
            LIMIT 50
        """, (job_id,))
        runs = [dict(row) for row in cursor.fetchall()]

        # Pass raw timestamps and format duration
        for run in runs:
            run['start_at_utc'] = run['start_at']
            run['finish_at_utc'] = run['finish_at']
            run['duration_formatted'] = format_duration(run['duration'])

    return template('job_runs', job=job, runs=runs)


@app.route('/run/<run_id:int>/logs')
def run_logs(run_id):
    """Show logs for a specific run"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get run details
        cursor.execute("""
            SELECT jr.*, j.name as job_name
            FROM job_runs jr
            JOIN jobs j ON jr.job_id = j.id
            WHERE jr.id = ?
        """, (run_id,))
        run = cursor.fetchone()
        if not run:
            redirect('/')
        run = dict(run)

        # Get logs
        cursor.execute("""
            SELECT * FROM run_logs
            WHERE run_id = ?
            ORDER BY timestamp
        """, (run_id,))
        logs = [dict(row) for row in cursor.fetchall()]

        # Pass raw timestamps for client-side conversion
        run['start_at_utc'] = run['start_at']
        run['finish_at_utc'] = run['finish_at']

        for log in logs:
            log['timestamp_utc'] = log['timestamp']

    return template('run_logs', run=run, logs=logs)


@app.route('/static/<filename>')
def server_static(filename):
    """Serve static files"""
    return static_file(filename, root=os.path.join(os.path.dirname(__file__), 'static'))


# JSON API endpoints for multi-instance manager
@app.route('/api/jobs')
def api_jobs():
    """Return all jobs as JSON"""
    response.content_type = 'application/json'
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY id")
        jobs = [dict(row) for row in cursor.fetchall()]

    # Enhance job data with formatted schedule
    for job in jobs:
        job['schedule_text'] = get_schedule_text(job)

    return json.dumps(jobs)


@app.route('/api/job/<job_id:int>')
def api_job(job_id):
    """Return single job as JSON"""
    response.content_type = 'application/json'
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        if not job:
            response.status = 404
            return json.dumps({'error': 'Job not found'})

        job = dict(job)
        job['schedule_text'] = get_schedule_text(job)

    return json.dumps(job)


@app.route('/api/job/<job_id:int>/runs')
def api_job_runs(job_id):
    """Return job runs as JSON"""
    response.content_type = 'application/json'
    with get_db() as conn:
        cursor = conn.cursor()

        # Get job details
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        if not job:
            response.status = 404
            return json.dumps({'error': 'Job not found'})
        job = dict(job)

        # Get runs
        cursor.execute("""
            SELECT * FROM job_runs
            WHERE job_id = ?
            ORDER BY start_at DESC
            LIMIT 50
        """, (job_id,))
        runs = [dict(row) for row in cursor.fetchall()]

        # Format duration
        for run in runs:
            run['duration_formatted'] = format_duration(run['duration'])

    return json.dumps({'job': job, 'runs': runs})


if __name__ == '__main__':
    # Initialize database
    init_database()

    # Run web server
    app.run(host='0.0.0.0', port=48080, debug=True)

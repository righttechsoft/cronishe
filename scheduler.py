import time
import subprocess
import threading
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import logging
import sys
from zoneinfo import ZoneInfo

from database import (
    init_database,
    get_db,
    create_job_run,
    finish_job_run,
    update_job_last_run,
    add_log_line
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def call_webhook(url: Optional[str], job_name: str, context: str):
    """Call a webhook URL if provided"""
    if not url:
        return

    try:
        response = requests.get(url, timeout=10)
        logger.info(f"Webhook {context} called for job '{job_name}': {url} (status: {response.status_code})")
    except Exception as e:
        logger.error(f"Failed to call webhook {context} for job '{job_name}': {e}")


def execute_job(job: Dict):
    """Execute a job as a subprocess with output capture"""
    job_id = job['id']
    job_name = job['name']
    job_path = job['path']

    logger.info(f"Starting job '{job_name}' (ID: {job_id})")

    # Create job run record
    run_id = create_job_run(job_id)

    # Call on_start webhook
    call_webhook(job['on_start'], job_name, 'on_start')

    try:
        # Start the process
        process = subprocess.Popen(
            job_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=True
        )

        # Capture output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                line = line.rstrip()
                logger.info(f"[{job_name}] {line}")
                add_log_line(run_id, line)

        # Wait for process to complete
        process.wait()

        # Determine result based on exit code
        result = 'success' if process.returncode == 0 else 'fail'

        # Update job run
        finish_job_run(run_id, result)
        update_job_last_run(job_id, result)

        logger.info(f"Job '{job_name}' finished with result: {result} (exit code: {process.returncode})")

        # Call appropriate webhook
        if result == 'success':
            call_webhook(job['on_success'], job_name, 'on_success')
        else:
            call_webhook(job['on_fail'], job_name, 'on_fail')

    except Exception as e:
        logger.error(f"Error executing job '{job_name}': {e}")
        add_log_line(run_id, f"ERROR: {str(e)}")
        finish_job_run(run_id, 'fail')
        update_job_last_run(job_id, 'fail')
        call_webhook(job['on_fail'], job_name, 'on_fail')


def should_run_job(job: Dict, current_time: datetime) -> bool:
    """Determine if a job should run based on its schedule"""
    job_id = job['id']
    job_name = job['name']

    if not job['active']:
        logger.debug(f"Job '{job_name}' (ID: {job_id}) is inactive, skipping")
        return False

    frequency_type = job['frequency_type']

    if frequency_type == 'every':
        # Run every N minutes
        every_min = job['frequency_every_min']
        if not every_min:
            logger.debug(f"Job '{job_name}' (ID: {job_id}) has no interval set, skipping")
            return False

        last_run = job['last_run']
        if not last_run:
            # Never run before, should run now
            logger.info(f"Job '{job_name}' (ID: {job_id}) has never run, scheduling now")
            return True

        # Parse last run time (stored as naive UTC)
        last_run_time = datetime.fromisoformat(last_run)

        # Calculate time difference (both are naive UTC)
        minutes_since_last_run = (current_time - last_run_time).total_seconds() / 60

        logger.info(f"Job '{job_name}' (ID: {job_id}): last_run={last_run}, current_time={current_time}, diff={minutes_since_last_run:.1f} min, interval={every_min} min")

        # Handle bad timestamps (last_run in the future) - likely from old code
        if minutes_since_last_run < 0:
            logger.warning(f"Job '{job_name}' (ID: {job_id}) has last_run in the future (corrupted timestamp), scheduling now to reset")
            return True

        # Check if enough time has passed
        if minutes_since_last_run >= every_min:
            logger.info(f"Job '{job_name}' (ID: {job_id}) is due (every {every_min} min, last run {minutes_since_last_run:.1f} min ago)")
            return True

    elif frequency_type == 'at':
        # Get job timezone, default to UTC
        job_tz = ZoneInfo(job['timezone']) if job.get('timezone') else ZoneInfo('UTC')

        # Convert current UTC time to job timezone for checking day/hour/minute
        current_aware = current_time.replace(tzinfo=ZoneInfo('UTC'))
        job_time = current_aware.astimezone(job_tz)

        current_weekday = job_time.weekday()  # 0=Monday, 6=Sunday
        current_hour = job_time.hour
        current_minute = job_time.minute

        # Map weekday to column name
        weekday_map = {
            0: 'frequency_at_mon',
            1: 'frequency_at_tue',
            2: 'frequency_at_wed',
            3: 'frequency_at_thu',
            4: 'frequency_at_fri',
            5: 'frequency_at_sat',
            6: 'frequency_at_sun'
        }

        # Check if this job is scheduled for this day of week (boolean check)
        day_enabled = job.get(weekday_map[current_weekday])
        if not day_enabled:
            logger.debug(f"Job '{job_name}' (ID: {job_id}) not scheduled for current weekday")
            return False

        scheduled_hour = job['frequency_at_hr']
        scheduled_minute = job['frequency_at_min']

        # Check if scheduled hour/minute are set
        if scheduled_hour is None or scheduled_minute is None:
            logger.debug(f"Job '{job_name}' (ID: {job_id}) has no time set, skipping")
            return False

        logger.debug(f"Job '{job_name}' (ID: {job_id}): current time {current_hour:02d}:{current_minute:02d}, scheduled {scheduled_hour:02d}:{scheduled_minute:02d}")

        # Check if current time matches schedule
        if current_hour == scheduled_hour and current_minute == scheduled_minute:
            # Check if already run in the last minute (use naive UTC for comparison)
            last_run = job['last_run']
            if last_run:
                last_run_time = datetime.fromisoformat(last_run)
                if (current_time - last_run_time).total_seconds() < 60:
                    logger.debug(f"Job '{job_name}' (ID: {job_id}) already ran in the last minute, skipping")
                    return False
            logger.info(f"Job '{job_name}' (ID: {job_id}) is due (scheduled at {scheduled_hour:02d}:{scheduled_minute:02d})")
            return True

    return False


def abort_running_jobs():
    """Mark all currently running jobs as aborted on scheduler startup"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Find all job runs that are still running (no finish_at)
        cursor.execute("""
            SELECT id, job_id FROM job_runs
            WHERE finish_at IS NULL
        """)
        running_jobs = cursor.fetchall()

        if running_jobs:
            logger.info(f"Found {len(running_jobs)} running job(s) from previous session, marking as aborted")

            for run in running_jobs:
                run_id = run['id']
                job_id = run['job_id']

                # Mark as failed/aborted
                cursor.execute("""
                    UPDATE job_runs
                    SET finish_at = ?, result = 'fail'
                    WHERE id = ?
                """, (datetime.now(timezone.utc).replace(tzinfo=None), run_id))

                # Add log entry
                cursor.execute("""
                    INSERT INTO run_logs (run_id, timestamp, log_line)
                    VALUES (?, ?, ?)
                """, (run_id, datetime.now(timezone.utc).replace(tzinfo=None), "Job aborted - scheduler restarted"))

                logger.info(f"Marked run ID {run_id} (job ID {job_id}) as aborted")

            conn.commit()
        else:
            logger.info("No running jobs from previous session")


def get_jobs_to_run() -> List[Dict]:
    """Get all jobs that should be executed now"""
    # Use naive UTC time for comparisons with database timestamps
    current_time = datetime.now(ZoneInfo('UTC')).replace(second=0, microsecond=0, tzinfo=None)
    jobs_to_run = []

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE active = 1")
        jobs = cursor.fetchall()

        logger.info(f"Checking {len(jobs)} active job(s) at {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        for job in jobs:
            job_dict = dict(job)
            if should_run_job(job_dict, current_time):
                jobs_to_run.append(job_dict)

        if jobs_to_run:
            logger.info(f"Found {len(jobs_to_run)} job(s) to run")
        else:
            logger.info("No jobs due to run at this time")

    return jobs_to_run


def scheduler_loop():
    """Main scheduler loop - runs every minute"""
    logger.info("Scheduler started")

    # Abort any jobs that were running when scheduler was stopped
    abort_running_jobs()

    # Check for jobs immediately on startup
    logger.info("Performing initial job check")
    jobs = get_jobs_to_run()
    for job in jobs:
        thread = threading.Thread(target=execute_job, args=(job,))
        thread.daemon = True
        thread.start()

    while True:
        try:
            # Wait until next minute
            current_time = datetime.now()
            next_minute = (current_time + timedelta(minutes=1)).replace(second=0, microsecond=0)
            sleep_seconds = (next_minute - current_time).total_seconds()

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

            # Get jobs that should run
            jobs = get_jobs_to_run()

            # Execute each job in a separate thread
            for job in jobs:
                thread = threading.Thread(target=execute_job, args=(job,))
                thread.daemon = True
                thread.start()

        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            time.sleep(60)


if __name__ == "__main__":
    # Initialize database
    init_database()
    logger.info("Database initialized")

    # Start scheduler
    scheduler_loop()

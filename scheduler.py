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
    add_log_line,
    is_job_running,
    schedule_retry,
    get_pending_retries,
    remove_retry,
    clear_retries_for_job,
    update_run_pid
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


def calculate_retry_delay(job: Dict, attempt_number: int) -> int:
    """
    Calculate smart retry delay in minutes to avoid clashing with regular scheduled runs.

    Args:
        job: Job dictionary with schedule information
        attempt_number: Current retry attempt (1, 2, 3, etc.)

    Returns:
        Delay in minutes before the retry should run
    """
    frequency_type = job['frequency_type']

    if frequency_type == 'every':
        # For 'every X minutes' jobs, use intervals smaller than X to avoid collision
        every_min = job.get('frequency_every_min', 60)

        if every_min <= 2:
            # Very frequent jobs (1-2 min): retry at 15s, 30s, 45s intervals (convert to fraction of minutes)
            # But we work in minutes, so use 1 min for all attempts to avoid complexity
            return 1
        elif every_min <= 5:
            # Frequent jobs (3-5 min): use 1, 2, 3 minutes
            delays = [1, 2, 3]
        else:
            # Less frequent jobs: use exponential backoff capped at half the interval
            # This ensures retries complete before next scheduled run
            max_delay = every_min // 2
            delays = [min(1 * (2 ** (i)), max_delay) for i in range(3)]

        # Return the delay for this attempt (attempt_number is 1-indexed)
        return delays[min(attempt_number - 1, len(delays) - 1)]

    else:  # 'at' type
        # For 'at' jobs, use standard exponential backoff: 1, 2, 4 minutes
        delays = [1, 2, 4]
        return delays[min(attempt_number - 1, len(delays) - 1)]


def call_webhook(url: Optional[str], job_name: str, context: str):
    """Call a webhook URL if provided, with retry logic"""
    if not url:
        return

    max_attempts = 3
    wait_times = [1, 3, 5]  # Increasing pauses: 1s, 3s, 5s

    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise exception for 4xx/5xx status codes
            logger.info(f"Webhook {context} called for job '{job_name}': {url} (status: {response.status_code}, attempt: {attempt + 1})")
            return  # Success, exit function
        except Exception as e:
            if attempt < max_attempts - 1:
                # Not the last attempt, wait and retry
                wait_time = wait_times[attempt]
                logger.warning(f"Webhook {context} for job '{job_name}' failed (attempt {attempt + 1}/{max_attempts}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Last attempt failed, log error
                logger.error(f"Webhook {context} for job '{job_name}' failed after {max_attempts} attempts: {e}")


def execute_job(job: Dict, is_retry: bool = False, retry_attempt: int = 0):
    """
    Execute a job as a subprocess with output capture.

    Args:
        job: Job dictionary with all job details
        is_retry: Whether this is a retry attempt (default: False)
        retry_attempt: The retry attempt number if is_retry=True (0 for regular run)
    """
    job_id = job['id']
    job_name = job['name']
    job_path = job['path']
    retry_count = job.get('retry_count', 3)

    retry_suffix = f" (retry {retry_attempt}/{retry_count})" if is_retry else ""
    logger.info(f"Starting job '{job_name}' (ID: {job_id}){retry_suffix}")

    # Track start time for duration calculation
    start_time = datetime.now(timezone.utc)

    # Create job run record
    run_id = create_job_run(job_id)

    # Add log line indicating if this is a retry
    if is_retry:
        add_log_line(run_id, f"RETRY ATTEMPT {retry_attempt}/{retry_count}")

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

        # Save the PID to the database for stop functionality
        update_run_pid(run_id, process.pid)
        logger.info(f"Job '{job_name}' started with PID {process.pid}")

        # Capture output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                line = line.rstrip()
                logger.info(f"[{job_name}] {line}")
                add_log_line(run_id, line)

        # Wait for process to complete
        process.wait()

        # Calculate duration in seconds
        end_time = datetime.now(timezone.utc)
        duration = int((end_time - start_time).total_seconds())

        # Determine result based on exit code
        result = 'success' if process.returncode == 0 else 'fail'

        # Update job run
        finish_job_run(run_id, result, duration)
        update_job_last_run(job_id, result)

        logger.info(f"Job '{job_name}' finished with result: {result} (exit code: {process.returncode}, duration: {duration}s)")

        # Handle retries based on result
        if result == 'success':
            # Clear any pending retries for this job since it succeeded
            clear_retries_for_job(job_id)
            call_webhook(job['on_success'], job_name, 'on_success')
        else:
            # Job failed
            call_webhook(job['on_fail'], job_name, 'on_fail')

            # Schedule retries if this was the initial run and retry_count > 0
            if not is_retry and retry_count > 0:
                # Clear any existing retries for this job first
                clear_retries_for_job(job_id)

                # Schedule retries
                for attempt in range(1, retry_count + 1):
                    delay_minutes = calculate_retry_delay(job, attempt)
                    retry_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=delay_minutes)
                    schedule_retry(job_id, run_id, attempt, retry_time)
                    logger.info(f"Scheduled retry {attempt}/{retry_count} for job '{job_name}' in {delay_minutes} minute(s) at {retry_time}")

            elif is_retry and retry_attempt < retry_count:
                # This was a retry that failed, but there are more retries left
                # The remaining retries are already scheduled in the queue, so just log
                logger.info(f"Job '{job_name}' retry {retry_attempt}/{retry_count} failed, {retry_count - retry_attempt} retry(s) remaining")
            elif is_retry and retry_attempt >= retry_count:
                # This was the last retry and it failed
                logger.error(f"Job '{job_name}' failed after {retry_count} retry attempts")

    except Exception as e:
        # Calculate duration even for failed jobs
        end_time = datetime.now(timezone.utc)
        duration = int((end_time - start_time).total_seconds())

        logger.error(f"Error executing job '{job_name}': {e}")
        add_log_line(run_id, f"ERROR: {str(e)}")
        finish_job_run(run_id, 'fail', duration)
        update_job_last_run(job_id, 'fail')
        call_webhook(job['on_fail'], job_name, 'on_fail')

        # Same retry logic as above for exception case
        if not is_retry and job.get('retry_count', 3) > 0:
            clear_retries_for_job(job_id)
            for attempt in range(1, retry_count + 1):
                delay_minutes = calculate_retry_delay(job, attempt)
                retry_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=delay_minutes)
                schedule_retry(job_id, run_id, attempt, retry_time)
                logger.info(f"Scheduled retry {attempt}/{retry_count} for job '{job_name}' in {delay_minutes} minute(s) at {retry_time}")


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

            # Get current time as naive UTC for retry checking
            current_utc = datetime.now(timezone.utc).replace(tzinfo=None)

            # Check for pending retries
            pending_retries = get_pending_retries(current_utc)
            if pending_retries:
                logger.info(f"Found {len(pending_retries)} pending retry(s)")

                for retry in pending_retries:
                    retry_id = retry['id']
                    job_id = retry['job_id']
                    attempt_number = retry['attempt_number']

                    # Get the job details
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                        job_row = cursor.fetchone()

                        if job_row:
                            job = dict(job_row)

                            # Check if job is already running before starting retry
                            if is_job_running(job_id):
                                logger.info(f"Job '{job['name']}' (ID: {job_id}) is already running, skipping retry {attempt_number}")
                                # Don't remove from queue yet - will retry next minute
                                continue

                            # Check if job is still active
                            if not job['active']:
                                logger.info(f"Job '{job['name']}' (ID: {job_id}) is inactive, canceling retry {attempt_number}")
                                remove_retry(retry_id)
                                continue

                            # Execute the retry in a separate thread
                            logger.info(f"Executing retry {attempt_number} for job '{job['name']}' (ID: {job_id})")
                            thread = threading.Thread(target=execute_job, args=(job, True, attempt_number))
                            thread.daemon = True
                            thread.start()

                            # Remove the retry from the queue
                            remove_retry(retry_id)
                        else:
                            # Job no longer exists, remove retry from queue
                            logger.warning(f"Job ID {job_id} not found, removing retry from queue")
                            remove_retry(retry_id)

            # Get jobs that should run
            jobs = get_jobs_to_run()

            # Execute each job in a separate thread
            for job in jobs:
                # Check if job is already running before starting
                if is_job_running(job['id']):
                    logger.info(f"Job '{job['name']}' (ID: {job['id']}) is already running, skipping")
                    continue
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

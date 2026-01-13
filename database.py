import sqlite3
import os
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Optional


DB_PATH = os.environ.get("DB_PATH", "cronishe.db")


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize database schema"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Create jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                frequency_type TEXT NOT NULL CHECK(frequency_type IN ('at', 'every')),
                frequency_every_min INTEGER,
                frequency_at_mon INTEGER CHECK(frequency_at_mon IN (0, 1)),
                frequency_at_tue INTEGER CHECK(frequency_at_tue IN (0, 1)),
                frequency_at_wed INTEGER CHECK(frequency_at_wed IN (0, 1)),
                frequency_at_thu INTEGER CHECK(frequency_at_thu IN (0, 1)),
                frequency_at_fri INTEGER CHECK(frequency_at_fri IN (0, 1)),
                frequency_at_sat INTEGER CHECK(frequency_at_sat IN (0, 1)),
                frequency_at_sun INTEGER CHECK(frequency_at_sun IN (0, 1)),
                frequency_at_hr INTEGER CHECK(frequency_at_hr BETWEEN 0 AND 23),
                frequency_at_min INTEGER CHECK(frequency_at_min BETWEEN 0 AND 59),
                timezone TEXT,
                last_run TIMESTAMP,
                last_run_result TEXT CHECK(last_run_result IN ('success', 'fail', NULL)),
                active INTEGER NOT NULL DEFAULT 1,
                retry_count INTEGER NOT NULL DEFAULT 3,
                on_start TEXT,
                on_success TEXT,
                on_fail TEXT
            )
        """)

        # Create job_runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                start_at TIMESTAMP,
                finish_at TIMESTAMP,
                duration INTEGER,
                result TEXT CHECK(result IN ('success', 'fail', 'aborted', NULL)),
                pid INTEGER,
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
        """)

        # Create run_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS run_logs (
                run_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                log_line TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES job_runs(id)
            )
        """)

        # Create retry_queue table to track pending retries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retry_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                run_id INTEGER NOT NULL,
                attempt_number INTEGER NOT NULL,
                retry_at TIMESTAMP NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs(id),
                FOREIGN KEY (run_id) REFERENCES job_runs(id)
            )
        """)

        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_runs_job_id ON job_runs(job_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_logs_run_id ON run_logs(run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_retry_queue_retry_at ON retry_queue(retry_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_retry_queue_job_id ON retry_queue(job_id)")

        # Add retry_count column if it doesn't exist (migration for existing databases)
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'retry_count' not in columns:
            cursor.execute("ALTER TABLE jobs ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 3")

        # Add pid column to job_runs if it doesn't exist (migration for existing databases)
        cursor.execute("PRAGMA table_info(job_runs)")
        run_columns = [row[1] for row in cursor.fetchall()]
        if 'pid' not in run_columns:
            cursor.execute("ALTER TABLE job_runs ADD COLUMN pid INTEGER")

        conn.commit()


def add_log_line(run_id: int, log_line: str):
    """Add a log line to run_logs"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO run_logs (run_id, timestamp, log_line) VALUES (?, ?, ?)",
            (run_id, datetime.now(timezone.utc).replace(tzinfo=None), log_line)
        )
        conn.commit()


def create_job_run(job_id: int) -> int:
    """Create a new job run record and return its ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO job_runs (job_id, start_at) VALUES (?, ?)",
            (job_id, datetime.now(timezone.utc).replace(tzinfo=None))
        )
        conn.commit()
        return cursor.lastrowid


def finish_job_run(run_id: int, result: str, duration: int):
    """Update job run with finish time, duration, and result"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE job_runs SET finish_at = ?, duration = ?, result = ? WHERE id = ?",
            (datetime.now(timezone.utc).replace(tzinfo=None), duration, result, run_id)
        )
        conn.commit()


def update_job_last_run(job_id: int, result: str):
    """Update job's last run timestamp and result"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE jobs SET last_run = ?, last_run_result = ? WHERE id = ?",
            (datetime.now(timezone.utc).replace(tzinfo=None), result, job_id)
        )
        conn.commit()


def is_job_running(job_id: int) -> bool:
    """Check if a job is currently running (has started but not finished)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM job_runs WHERE job_id = ? AND start_at IS NOT NULL AND finish_at IS NULL",
            (job_id,)
        )
        count = cursor.fetchone()[0]
        return count > 0




def schedule_retry(job_id: int, run_id: int, attempt_number: int, retry_at: datetime):
    """Schedule a retry for a failed job"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO retry_queue (job_id, run_id, attempt_number, retry_at) VALUES (?, ?, ?, ?)",
            (job_id, run_id, attempt_number, retry_at)
        )
        conn.commit()


def get_pending_retries(current_time: datetime):
    """Get all retries that are due to run"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM retry_queue WHERE retry_at <= ?",
            (current_time,)
        )
        return [dict(row) for row in cursor.fetchall()]


def remove_retry(retry_id: int):
    """Remove a retry from the queue"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM retry_queue WHERE id = ?", (retry_id,))
        conn.commit()


def clear_retries_for_job(job_id: int):
    """Clear all pending retries for a job"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM retry_queue WHERE job_id = ?", (job_id,))
        conn.commit()


def update_run_pid(run_id: int, pid: int):
    """Update the PID for a running job"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE job_runs SET pid = ? WHERE id = ?",
            (pid, run_id)
        )
        conn.commit()


def get_run_pid(run_id: int) -> Optional[int]:
    """Get the PID for a running job"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT pid FROM job_runs WHERE id = ?",
            (run_id,)
        )
        row = cursor.fetchone()
        return row['pid'] if row else None


def abort_run(run_id: int, duration: int):
    """Mark a run as aborted"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE job_runs SET finish_at = ?, duration = ?, result = 'aborted', pid = NULL WHERE id = ?",
            (datetime.now(timezone.utc).replace(tzinfo=None), duration, run_id)
        )
        conn.commit()


def get_running_run(run_id: int) -> Optional[dict]:
    """Get a running job run by ID (with start_at but no finish_at)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM job_runs WHERE id = ? AND start_at IS NOT NULL AND finish_at IS NULL",
            (run_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

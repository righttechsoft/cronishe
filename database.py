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
                result TEXT CHECK(result IN ('success', 'fail', NULL)),
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

        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_runs_job_id ON job_runs(job_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_logs_run_id ON run_logs(run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(active)")

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

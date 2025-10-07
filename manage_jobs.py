#!/usr/bin/env python3
"""
Job management utility for cronishe.
Add, list, update, and delete scheduled jobs.
"""
import argparse
import sys
from datetime import datetime
from database import init_database, get_db


def add_job(args):
    """Add a new job to the database"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Build the INSERT query based on frequency type
        if args.frequency_type == 'every':
            cursor.execute("""
                INSERT INTO jobs (name, path, frequency_type, frequency_every_min, active, on_start, on_success, on_fail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (args.name, args.path, 'every', args.every, 1, args.on_start, args.on_success, args.on_fail))
        else:  # 'at'
            # Parse days (e.g., "mon,wed,fri")
            days = {}
            if args.days:
                for day in args.days.split(','):
                    day = day.strip().lower()
                    days[f'frequency_at_{day}'] = args.hour

            cursor.execute(f"""
                INSERT INTO jobs (name, path, frequency_type,
                    frequency_at_mon, frequency_at_tue, frequency_at_wed, frequency_at_thu,
                    frequency_at_fri, frequency_at_sat, frequency_at_sun,
                    frequency_at_hr, frequency_at_min, active, on_start, on_success, on_fail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                args.name, args.path, 'at',
                days.get('frequency_at_mon'), days.get('frequency_at_tue'),
                days.get('frequency_at_wed'), days.get('frequency_at_thu'),
                days.get('frequency_at_fri'), days.get('frequency_at_sat'),
                days.get('frequency_at_sun'),
                args.hour, args.minute, 1, args.on_start, args.on_success, args.on_fail
            ))

        conn.commit()
        print(f"Job '{args.name}' added successfully (ID: {cursor.lastrowid})")


def list_jobs(args):
    """List all jobs"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY id")
        jobs = cursor.fetchall()

        if not jobs:
            print("No jobs found")
            return

        print(f"\n{'ID':<5} {'Name':<20} {'Type':<6} {'Schedule':<30} {'Active':<8} {'Last Run':<20} {'Result':<10}")
        print("-" * 110)

        for job in jobs:
            job_id = job['id']
            name = job['name']
            freq_type = job['frequency_type']
            active = 'Yes' if job['active'] else 'No'
            last_run = job['last_run'] or 'Never'
            if last_run != 'Never':
                last_run = datetime.fromisoformat(last_run).strftime('%Y-%m-%d %H:%M')
            result = job['last_run_result'] or '-'

            if freq_type == 'every':
                schedule = f"Every {job['frequency_every_min']} minutes"
            else:
                days = []
                for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
                    if job[f'frequency_at_{day}'] is not None:
                        days.append(day)
                schedule = f"{','.join(days)} at {job['frequency_at_hr']}:{job['frequency_at_min']:02d}" if days else "Not scheduled"

            print(f"{job_id:<5} {name:<20} {freq_type:<6} {schedule:<30} {active:<8} {last_run:<20} {result:<10}")


def toggle_job(args):
    """Enable or disable a job"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE jobs SET active = ? WHERE id = ?", (args.enable, args.job_id))
        conn.commit()

        if cursor.rowcount > 0:
            status = "enabled" if args.enable else "disabled"
            print(f"Job {args.job_id} {status}")
        else:
            print(f"Job {args.job_id} not found")


def delete_job(args):
    """Delete a job"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE id = ?", (args.job_id,))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Job {args.job_id} deleted")
        else:
            print(f"Job {args.job_id} not found")


def view_logs(args):
    """View logs for a job run"""
    with get_db() as conn:
        cursor = conn.cursor()

        if args.run_id:
            # Show logs for specific run
            cursor.execute("""
                SELECT rl.timestamp, rl.log_line
                FROM run_logs rl
                WHERE rl.run_id = ?
                ORDER BY rl.timestamp
            """, (args.run_id,))

            logs = cursor.fetchall()
            if not logs:
                print(f"No logs found for run {args.run_id}")
                return

            print(f"\nLogs for run {args.run_id}:")
            print("-" * 80)
            for log in logs:
                timestamp = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] {log['log_line']}")

        else:
            # Show recent runs for job
            cursor.execute("""
                SELECT jr.id, jr.start_at, jr.finish_at, jr.result
                FROM job_runs jr
                WHERE jr.job_id = ?
                ORDER BY jr.start_at DESC
                LIMIT ?
            """, (args.job_id, args.limit))

            runs = cursor.fetchall()
            if not runs:
                print(f"No runs found for job {args.job_id}")
                return

            print(f"\nRecent runs for job {args.job_id}:")
            print(f"{'Run ID':<8} {'Start':<20} {'Finish':<20} {'Result':<10}")
            print("-" * 60)
            for run in runs:
                start = datetime.fromisoformat(run['start_at']).strftime('%Y-%m-%d %H:%M:%S')
                finish = datetime.fromisoformat(run['finish_at']).strftime('%Y-%m-%d %H:%M:%S') if run['finish_at'] else 'Running'
                result = run['result'] or '-'
                print(f"{run['id']:<8} {start:<20} {finish:<20} {result:<10}")


def main():
    parser = argparse.ArgumentParser(description='Manage cronishe jobs')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Add job
    add_parser = subparsers.add_parser('add', help='Add a new job')
    add_parser.add_argument('name', help='Job name')
    add_parser.add_argument('path', help='Path to executable/script')
    add_parser.add_argument('frequency_type', choices=['every', 'at'], help='Frequency type')
    add_parser.add_argument('--every', type=int, help='Run every N minutes (for "every" type)')
    add_parser.add_argument('--days', help='Days to run (comma-separated: mon,tue,wed,thu,fri,sat,sun)')
    add_parser.add_argument('--hour', type=int, help='Hour to run (0-23, for "at" type)')
    add_parser.add_argument('--minute', type=int, default=0, help='Minute to run (0-59, for "at" type)')
    add_parser.add_argument('--on-start', help='URL to call when job starts')
    add_parser.add_argument('--on-success', help='URL to call when job succeeds')
    add_parser.add_argument('--on-fail', help='URL to call when job fails')

    # List jobs
    list_parser = subparsers.add_parser('list', help='List all jobs')

    # Enable job
    enable_parser = subparsers.add_parser('enable', help='Enable a job')
    enable_parser.add_argument('job_id', type=int, help='Job ID')

    # Disable job
    disable_parser = subparsers.add_parser('disable', help='Disable a job')
    disable_parser.add_argument('job_id', type=int, help='Job ID')

    # Delete job
    delete_parser = subparsers.add_parser('delete', help='Delete a job')
    delete_parser.add_argument('job_id', type=int, help='Job ID')

    # View logs
    logs_parser = subparsers.add_parser('logs', help='View job run logs')
    logs_parser.add_argument('--job-id', type=int, help='Job ID (show recent runs)')
    logs_parser.add_argument('--run-id', type=int, help='Run ID (show logs for specific run)')
    logs_parser.add_argument('--limit', type=int, default=10, help='Number of recent runs to show')

    args = parser.parse_args()

    # Initialize database
    init_database()

    if args.command == 'add':
        add_job(args)
    elif args.command == 'list':
        list_jobs(args)
    elif args.command == 'enable':
        args.enable = 1
        toggle_job(args)
    elif args.command == 'disable':
        args.enable = 0
        toggle_job(args)
    elif args.command == 'delete':
        delete_job(args)
    elif args.command == 'logs':
        view_logs(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

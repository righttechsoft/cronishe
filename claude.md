# Cronishe - Advanced Cron Replacement

## Project Overview

Cronishe is a Python-based advanced cron replacement system with SQLite database backend, real-time log capture, timezone support, webhook notifications, and a web-based management interface.

## Architecture

### Core Components

1. **Database Layer** (`database.py`)
   - SQLite-based persistence
   - Context manager for connections
   - CRUD operations for jobs, runs, and logs
   - Naive UTC timestamp storage

2. **Scheduler** (`scheduler.py`)
   - Main event loop running every minute
   - Job execution engine with parallel processing
   - Timezone-aware scheduling
   - Webhook integration
   - Startup recovery and logging

3. **Web UI** (`webui.py`)
   - Bottle-based web framework
   - Job management interface with timezone conversion
   - Run history and log viewer
   - RESTful routes for CRUD operations
   - JSON API endpoints for multi-instance manager
   - Logo and favicon support

4. **Multi-Instance Manager** (`manager.py`)
   - Dashboard for monitoring multiple Cronishe instances
   - Aggregates jobs from all configured instances
   - Uses JSON API endpoints from webui.py
   - Configurable via environment variables
   - Runs on separate port (default: 48090)

5. **CLI Tool** (`manage_jobs.py`) - Optional
   - Command-line job management
   - Not required for normal operation (use Web UI instead)

## Database Schema

### Table: `jobs`

Stores job definitions and schedules.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment job ID |
| `name` | TEXT NOT NULL | Human-readable job name |
| `path` | TEXT NOT NULL | Command or script path to execute |
| `frequency_type` | TEXT NOT NULL | Schedule type: `'at'` or `'every'` |
| `frequency_every_min` | INTEGER | Interval in minutes (for `every` type) |
| `frequency_at_mon` | INTEGER (0/1) | Boolean: run on Monday |
| `frequency_at_tue` | INTEGER (0/1) | Boolean: run on Tuesday |
| `frequency_at_wed` | INTEGER (0/1) | Boolean: run on Wednesday |
| `frequency_at_thu` | INTEGER (0/1) | Boolean: run on Thursday |
| `frequency_at_fri` | INTEGER (0/1) | Boolean: run on Friday |
| `frequency_at_sat` | INTEGER (0/1) | Boolean: run on Saturday |
| `frequency_at_sun` | INTEGER (0/1) | Boolean: run on Sunday |
| `frequency_at_hr` | INTEGER (0-23) | Hour component for `at` schedules |
| `frequency_at_min` | INTEGER (0-59) | Minute component for `at` schedules |
| `timezone` | TEXT | IANA timezone (e.g., `UTC`, `America/New_York`) |
| `last_run` | TIMESTAMP | Last execution timestamp |
| `last_run_result` | TEXT | Last result: `'success'` or `'fail'` |
| `active` | INTEGER (0/1) | Boolean: job enabled/disabled |
| `on_start` | TEXT | Webhook URL called when job starts |
| `on_success` | TEXT | Webhook URL called on success |
| `on_fail` | TEXT | Webhook URL called on failure |

**Indexes:**
- `idx_jobs_active` on `active` column

### Table: `job_runs`

Tracks individual job executions.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment run ID |
| `job_id` | INTEGER NOT NULL | Foreign key to `jobs.id` |
| `timestamp` | TIMESTAMP | Record creation time (auto) |
| `start_at` | TIMESTAMP | Job execution start time |
| `finish_at` | TIMESTAMP | Job execution finish time |
| `duration` | INTEGER | Execution duration in seconds |
| `result` | TEXT | Execution result: `'success'` or `'fail'` |

**Indexes:**
- `idx_job_runs_job_id` on `job_id` column

### Table: `run_logs`

Stores line-by-line output from job executions.

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | INTEGER NOT NULL | Foreign key to `job_runs.id` |
| `timestamp` | TIMESTAMP | Log line timestamp (auto) |
| `log_line` | TEXT NOT NULL | Output line content |

**Indexes:**
- `idx_run_logs_run_id` on `run_id` column

## File Structure

```
cronishe/
├── database.py          # Database operations and schema
├── scheduler.py         # Main scheduler loop and job execution
├── webui.py            # Web UI application with API endpoints
├── manager.py          # Multi-instance manager dashboard
├── entrypoint.sh       # Docker entrypoint (runs both scheduler and webui)
├── manage_jobs.py      # CLI management tool (optional)
├── example_job.py      # Example test job
├── pyproject.toml      # Python dependencies (uv)
├── Dockerfile          # Container image definition
├── docker-compose.yml  # Docker deployment config
├── .dockerignore       # Docker build exclusions
├── .gitignore          # Git exclusions
├── claude.md           # This documentation
├── README.md           # User documentation
├── static/             # Static assets
│   ├── logo.png        # Application logo
│   ├── favicon-16x16.png
│   ├── favicon-32x32.png
│   ├── apple-touch-icon.png
│   └── site.webmanifest
└── templates/          # Bottle templates
    ├── index.tpl       # Job listing page
    ├── add_job.tpl     # Add job form
    ├── edit_job.tpl    # Edit job form
    ├── job_runs.tpl    # Run history page
    ├── run_logs.tpl    # Log viewer page
    └── manager_index.tpl # Manager dashboard page
```

## Core Logic

### Scheduler Loop (`scheduler.py`)

#### Startup Sequence
1. Initialize database schema
2. Abort any jobs left running from previous session (mark as `result='fail'`)
3. Perform immediate job check (catch up on missed jobs)
4. Enter main loop

#### Main Loop
1. Runs infinitely, checking every minute (at second 0)
2. Queries database for all active jobs
3. Evaluates each job's schedule against current time
4. Spawns threads for jobs that should run
5. Sleeps until next minute boundary

#### Logging
- Comprehensive INFO-level logging for all scheduler events
- Job check summary: number of active jobs, current time
- Individual job evaluation: last run time, time difference, intervals
- Job execution: start, finish, result, webhooks
- Debug logging available for detailed troubleshooting
- Warnings for corrupted timestamps (last_run in future)

#### Job Scheduling Logic

**For `every` type jobs:**
- Check if `frequency_every_min` is set
- Calculate minutes elapsed since `last_run`
- If elapsed >= interval, job should run
- First run (no `last_run`): always executes
- **Error Recovery**: Detects corrupted timestamps (last_run in future) and auto-schedules to reset

**For `at` type jobs:**
- Convert current UTC time to job's timezone
- Get current weekday (0=Monday, 6=Sunday)
- Check if corresponding day boolean is enabled (e.g., `frequency_at_mon`)
- Compare current hour/minute with `frequency_at_hr`/`frequency_at_min`
- Prevent duplicate runs within same minute using `last_run`

**Missed Job Recovery:**
- On scheduler startup, performs immediate job check
- Catches up on jobs that should have run while scheduler was stopped
- For `every` type: runs if time elapsed exceeds interval
- For `at` type: runs if current time matches schedule and hasn't run in last 60 seconds

#### Job Execution Process

1. **Pre-execution:**
   - Track start time for duration calculation
   - Create `job_runs` record with `start_at` timestamp
   - Call `on_start` webhook (if configured)

2. **Execution:**
   - Launch subprocess using `subprocess.Popen`
   - Set `shell=True` for command execution
   - Redirect stderr to stdout for unified capture
   - Stream output line-by-line in real-time
   - Save each line to `run_logs` table
   - Wait for process completion

3. **Post-execution:**
   - Calculate execution duration in seconds
   - Capture exit code (0 = success, non-zero = fail)
   - Update `job_runs` with `finish_at`, `duration`, and `result`
   - Update `jobs` with `last_run` and `last_run_result`
   - Call `on_success` or `on_fail` webhook based on result
   - Log duration in scheduler output

### Timezone Handling

**Database Storage:**
- All timestamps stored as **naive UTC** (no timezone info attached)
- Format: `YYYY-MM-DD HH:MM:SS.ffffff` (ISO format without 'Z')
- Uses `datetime.now(timezone.utc).replace(tzinfo=None)` for consistency
- Naive timestamps avoid timezone-aware/naive comparison issues in SQLite

**Scheduler:**
- Current time obtained as naive UTC via `datetime.now(ZoneInfo('UTC')).replace(tzinfo=None)`
- For `every` type: simple naive UTC timestamp subtraction
- For `at` type: temporarily converts to job's timezone to check day/hour/minute
- Job timezone specified in `jobs.timezone` field (IANA format, e.g., `America/New_York`)
- Defaults to UTC if timezone not specified
- Uses Python's `zoneinfo` module (Python 3.9+)
- `tzdata` package required on Windows

**Web UI:**
- Server sends raw UTC timestamps to browser
- JavaScript detects browser timezone using `Intl.DateTimeFormat().resolvedOptions().timeZone`
- Client-side conversion to local time on page load
- Displays timezone indicator in page header

### Webhook System

- HTTP GET requests to configured URLs
- 10-second timeout per request
- Three webhook types:
  - `on_start`: Called when job begins execution
  - `on_success`: Called when job exits with code 0
  - `on_fail`: Called when job exits with non-zero code
- Errors logged but do not affect job execution
- Optional: webhooks can be NULL/empty

### Parallel Execution

- Each job runs in separate daemon thread
- Multiple jobs can execute simultaneously
- No limit on concurrent jobs (system resources permitting)
- Thread-safe database operations via connection context managers
- Threads do not block main scheduler loop

## Web UI (`webui.py`)

### Routes

#### Web UI Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | List all jobs with duration info |
| `/job/add` | GET | Show add job form |
| `/job/add` | POST | Create new job |
| `/job/<id>/edit` | GET | Show edit job form |
| `/job/<id>/edit` | POST | Update job |
| `/job/<id>/toggle` | GET | Enable/disable job |
| `/job/<id>/delete` | POST | Delete job |
| `/job/<id>/runs` | GET | View job run history with duration |
| `/run/<id>/logs` | GET | View run logs |
| `/static/<filename>` | GET | Serve static assets |

#### JSON API Routes (for manager.py)

| Route | Method | Description |
|-------|--------|-------------|
| `/api/jobs` | GET | Return all jobs as JSON |
| `/api/job/<id>` | GET | Return single job as JSON |
| `/api/job/<id>/runs` | GET | Return job runs with duration as JSON |

### Template System

- Uses Bottle's built-in SimpleTemplate engine
- Templates in `templates/` directory
- `.tpl` extension
- Python expressions in `{{}}` and `% %` blocks
- No authentication/authorization implemented

### UI Features

- **Job List**: Table view with status, schedule, last run, and duration (HH:MM:SS)
- **Add/Edit Forms**: Dynamic schedule type switching (JavaScript)
- **Run History**: Chronological list of executions with duration in HH:MM:SS format
- **Duration Display**: Execution time shown in HH:MM:SS format (e.g., 00:02:35)
- **Log Viewer**: Terminal-style output with timestamps
- **Responsive Design**: Modern CSS, card-based layout
- **Color Coding**: Status badges, success/fail indicators
- **Timezone Display**: Shows browser timezone, converts all UTC times to local
- **Branding**: Logo display on all pages, favicon support (multiple sizes)

### Static Assets

- **Logo**: `/static/logo.png` displayed in page headers (40px height)
- **Favicons**: Multiple sizes for different devices
  - `/static/favicon-16x16.png`
  - `/static/favicon-32x32.png`
  - `/static/apple-touch-icon.png` (180x180)
  - `/static/site.webmanifest` - PWA manifest

## Standards and Conventions

### Code Style

- Python 3.9+ required
- Type hints in function signatures
- Docstrings for all functions
- PEP 8 naming conventions
- Context managers for database connections

### Error Handling

- Try/except blocks around job execution
- Errors logged via Python `logging` module
- Failed jobs marked with `result='fail'`
- Scheduler continues on individual job failures
- Main loop catches all exceptions to prevent crashes

### Logging

- Module: Python standard `logging`
- Level: INFO
- Format: `%(asctime)s - %(levelname)s - %(message)s`
- Output: stdout (for Docker compatibility)
- Logs: scheduler events, job execution, webhook calls

### Database Operations

- All operations use context managers (`with get_db()`)
- Auto-commit after writes
- Row factory set to `sqlite3.Row` for dict-like access
- Prepared statements with `?` placeholders (SQL injection safe)
- Foreign keys defined but not enforced (SQLite default)

## Dependencies

Managed via `pyproject.toml` for `uv`:

- `requests>=2.31.0` - HTTP client for webhooks
- `bottle>=0.12.25` - Web framework
- `tzdata>=2023.3` - Timezone database (Windows only)

Python standard library:
- `sqlite3` - Database
- `subprocess` - Job execution
- `threading` - Parallel execution
- `logging` - Event logging
- `zoneinfo` - Timezone support (Python 3.9+)

## Deployment

### Local Development

```bash
# Install dependencies
uv pip install -r pyproject.toml

# Run scheduler
python scheduler.py

# Run web UI (separate terminal)
python webui.py
```

### Docker

```bash
# Build and run
docker-compose up -d

# View logs (both scheduler and webui)
docker-compose logs -f

# Stop
docker-compose down
```

The Docker container runs both the scheduler and web UI together.

**Docker Configuration:**
- Base image: `python:3.11-slim`
- Package manager: `uv` (copied from official image)
- Volume mount: `./data:/app/data` for database persistence
- Port mapping: `48080:48080` (web UI)
- Environment: `DB_PATH=/app/data/cronishe.db`
- Entrypoint: `entrypoint.sh` - starts both scheduler and webui processes
- Access web UI at: `http://localhost:48080`

## Multi-Instance Manager (`manager.py`)

The manager provides a unified dashboard to monitor multiple Cronishe instances from a single interface.

### Configuration

Configured via environment variables:
- `CRONISHE_INSTANCES`: Comma-separated list in format `name1:url1,name2:url2`
- `MANAGER_PORT`: Port for manager web interface (default: `48090`)

### Features

- Aggregates jobs from all configured instances
- Displays instance name, URL, and job grid for each instance
- Shows job status, schedule, last run, and result
- Provides direct links to open individual instances
- Error handling for unreachable instances
- Browser timezone conversion for all timestamps
- Read-only view (no job editing from manager)

### Architecture

- Fetches data from `/api/jobs` endpoint of each instance
- 5-second timeout per instance request
- Displays jobs in grid format per instance
- Continues functioning even if some instances are unreachable
- Uses `requests` library for HTTP calls
- Renders via `manager_index.tpl` template

### Use Cases

- Multi-environment monitoring (production, staging, development)
- Multi-server monitoring (multiple production servers)
- Multi-tenant monitoring (different client instances)

### Limitations

- Read-only (no job creation/editing)
- Manual refresh (no auto-refresh)
- No aggregated statistics
- No authentication
- 5-second timeout per instance

## Environment Variables

### Cronishe Scheduler/WebUI

- `DB_PATH`: SQLite database file path (default: `cronishe.db`)

### Multi-Instance Manager

- `CRONISHE_INSTANCES`: Comma-separated instance list (default: `Local:http://localhost:48080`)
  - Format: `name1:url1,name2:url2,name3:url3`
  - Example: `Prod:http://prod:48080,Dev:http://localhost:48080`
- `MANAGER_PORT`: Manager web interface port (default: `48090`)

## Security Considerations

- **No Authentication**: Web UI has no auth (single-user design)
- **Shell Execution**: Jobs run via `shell=True` (trusted input only)
- **Webhook URLs**: No validation (ensure HTTPS for sensitive endpoints)
- **Database Access**: No encryption at rest
- **Network Exposure**: Web UI listens on `0.0.0.0` (all interfaces)

## Limitations

- Single database file (no distributed support)
- No job prioritization or resource limits
- No built-in job dependencies
- No retry logic for failed jobs
- No job timeout enforcement
- No rate limiting on webhooks
- No email notifications (webhooks only)

## Future Enhancement Ideas

- Job timeout configuration
- Retry logic with backoff
- Job dependencies (run after X succeeds)
- Resource limits (max concurrent jobs)
- Email notifications
- Job output retention policy
- Audit log for job changes
- API key authentication
- Job categories/tags
- Search and filtering
- Real-time run monitoring (WebSockets)
- Prometheus metrics endpoint

## Key Features & Improvements

### Scheduler Reliability
- **Startup Recovery**: Automatically aborts incomplete jobs from previous sessions
- **Immediate Check**: Catches up on missed jobs when scheduler starts
- **Error Detection**: Identifies and auto-corrects corrupted timestamps
- **Comprehensive Logging**: Detailed INFO-level logs for all scheduler events

### Timezone Support
- **Naive UTC Storage**: Avoids timezone-aware/naive comparison issues
- **Per-Job Timezones**: Each job can have its own timezone for `at` schedules
- **Browser Timezone Detection**: UI automatically shows times in user's local timezone
- **Consistent Time Handling**: All time comparisons use naive UTC for reliability

### User Interface
- **Auto Timezone Conversion**: JavaScript converts all UTC times to browser timezone
- **Visual Timezone Indicator**: Shows current timezone in page header
- **Duration Tracking**: Execution time stored in seconds, displayed in HH:MM:SS format
- **Logo & Branding**: Favicon and logo support on all pages
- **Real-time Updates**: Dynamic schedule type switching in forms

### Multi-Instance Management
- **Unified Dashboard**: Monitor multiple Cronishe instances from single interface
- **Aggregated View**: See jobs from all instances in one place
- **Flexible Configuration**: Environment variable-based instance configuration
- **Error Resilience**: Continues functioning even if some instances are unreachable
- **Instance Links**: Direct links to individual instance interfaces

## Troubleshooting

### Jobs Not Running

1. Check job is `active=1` in database
2. Verify schedule is correctly configured
3. Check timezone setting
4. **Review scheduler logs** - comprehensive logging shows:
   - Number of active jobs being checked each minute
   - Individual job evaluation (time since last run, interval)
   - Reasons jobs are skipped (inactive, wrong day, etc.)
   - Jobs that are scheduled to run
5. Ensure script path is absolute and accessible
6. Look for warnings about corrupted timestamps (last_run in future)
7. Check if scheduler aborted any incomplete runs on startup

### Logs Not Appearing

1. Verify job outputs to stdout/stderr
2. Check script has execute permissions
3. Use `print()` in Python scripts, not file writes
4. Ensure buffering is disabled (use `python -u`)

### Webhook Failures

1. Check URL is accessible from scheduler
2. Verify 10-second timeout is sufficient
3. Review scheduler logs for error details
4. Test webhook endpoint manually

### Database Locked

1. Ensure only one scheduler instance running
2. Check for long-running database operations
3. Use connection context managers properly
4. Consider WAL mode for concurrent access

## Development Guidelines

### Adding New Features

1. Update database schema in `database.py`
2. Add migration logic if modifying existing tables
3. Update templates if UI changes required
4. Add routes in `webui.py` for new endpoints
5. Update this documentation

### Testing Jobs

Use `example_job.py` as template:
- Print output for logging
- Use `sys.exit(0)` for success
- Use `sys.exit(1)` for failure
- Test with both schedule types

### Debugging

1. Run scheduler with `python scheduler.py` (not in background)
2. Watch console output for real-time logs (INFO level by default)
3. For detailed troubleshooting, change logging level to DEBUG in scheduler.py:
   ```python
   logging.basicConfig(level=logging.DEBUG, ...)
   ```
4. Query `job_runs` and `run_logs` tables directly:
   ```sql
   SELECT * FROM job_runs WHERE job_id = 1 ORDER BY start_at DESC LIMIT 10;
   SELECT * FROM run_logs WHERE run_id = 5 ORDER BY timestamp;
   ```
5. Use `sqlite3` CLI for database inspection
6. Check file permissions on job scripts
7. Look for scheduler startup messages indicating aborted jobs
8. Monitor webhook call success/failure in logs

## License

Not specified - add LICENSE file as needed.

## Version

Current version: 0.1.0 (from `pyproject.toml`)

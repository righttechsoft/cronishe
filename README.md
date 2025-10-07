# Cronishe

**Cronishe** is an advanced cron replacement system with a modern web interface, real-time log capture, timezone support, and webhook notifications.

## Purpose

Traditional cron has limitations: no centralized logging, no web interface, timezone complexity, and no execution history. Cronishe solves these problems by providing:

- **Web-based Management**: Add, edit, and monitor jobs through a browser
- **Real-time Logging**: Capture and view stdout/stderr from every job execution
- **Execution History**: Track all runs with timestamps, duration, and success/failure status
- **Timezone Support**: Schedule jobs in any timezone with automatic conversion
- **Webhook Integration**: Trigger HTTP notifications on job start, success, or failure
- **Startup Recovery**: Automatically handles jobs that were running when the scheduler stopped

## Key Features

### Scheduling
- **Two schedule types**:
  - `every N minutes`: Run at fixed intervals (e.g., every 15 minutes)
  - `at HH:MM on days`: Run at specific times on selected weekdays (e.g., 9:00 AM Mon-Fri)
- **Per-job timezones**: Each job can use its own timezone
- **Missed job recovery**: Catches up on jobs that should have run while scheduler was stopped
- **Enable/disable**: Toggle jobs on and off without deleting them

### Monitoring
- **Live log capture**: See stdout/stderr output in real-time
- **Run history**: View all past executions with results
- **Status indicators**: Visual success/fail badges
- **Browser timezone conversion**: All times automatically shown in your local timezone

### Integration
- **Webhooks**: HTTP GET requests on job events (start/success/fail)
- **Parallel execution**: Multiple jobs run simultaneously
- **Shell commands**: Execute any command or script

## Architecture

### Components

```
┌─────────────────┐
│   Web UI        │  Port 48080 - Bottle framework
│   (webui.py)    │  Job management interface
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SQLite DB     │  cronishe.db
│  (database.py)  │  Jobs, runs, logs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Scheduler     │  Main event loop
│ (scheduler.py)  │  Checks every minute
└─────────────────┘
```

### Database Schema

**jobs**: Job definitions with schedule and webhook configuration
**job_runs**: Execution records with start/finish times and results
**run_logs**: Line-by-line output from job executions

All timestamps stored as naive UTC for consistency. See `CLAUDE.md` for detailed schema.

### Technologies

- **Python 3.9+**: Core runtime with zoneinfo for timezone support
- **SQLite**: Lightweight, embedded database
- **Bottle**: Minimalist web framework
- **Threading**: Parallel job execution
- **subprocess**: Command execution with real-time output capture

## How to Run

### Option 1: Docker (Recommended)

**Quick Start:**

```bash
# Start the scheduler and web UI
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Access the web UI:** http://localhost:48080

**Data Persistence:** Jobs and logs are stored in `./data/cronishe.db` (mounted as volume)

### Option 2: Local Development

**Requirements:**
- Python 3.9 or higher
- uv package manager (or pip)

**Setup:**

```bash
# Install dependencies
uv pip install -r pyproject.toml
# OR
pip install requests bottle tzdata

# Run scheduler (in one terminal)
python scheduler.py

# Run web UI (in another terminal)
python webui.py
```

**Access the web UI:** http://localhost:48080

**Database location:** `cronishe.db` in current directory (or set `DB_PATH` env var)

### Option 3: Integration with Existing Dockerfile

Replace traditional cron in your existing Docker images with Cronishe.

#### Method 1: Clone from GitHub

```dockerfile
# Install Cronishe dependencies and clone repo
RUN apt-get update && apt-get install -y git && \
    git clone https://github.com/righttechsoft/cronishe.git /opt/cronishe && \
    pip install -r /opt/cronishe/pyproject.toml

# Start Cronishe alongside your application
CMD ["sh", "-c", "python /opt/cronishe/scheduler.py & python /opt/cronishe/webui.py & your-app-command"]
```

#### Method 2: Multi-stage Build

```dockerfile
FROM python:3.11-slim as cronishe
WORKDIR /cronishe
RUN apt-get update && apt-get install -y git && \
    git clone https://github.com/righttechsoft/cronishe.git . && \
    pip install uv && uv pip install --system -r pyproject.toml

FROM python:3.11-slim
# Your existing application setup...
COPY --from=cronishe /cronishe /opt/cronishe
COPY --from=cronishe /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Start both your app and Cronishe
CMD ["sh", "-c", "python /opt/cronishe/scheduler.py & python /opt/cronishe/webui.py & your-app-command"]
```

#### Method 3: Custom Entrypoint

```dockerfile
# In your existing Dockerfile
RUN pip install requests bottle tzdata && \
    cd /opt && git clone https://github.com/righttechsoft/cronishe.git

# Use custom entrypoint to start Cronishe alongside your app
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
```

**entrypoint.sh:**
```bash
#!/bin/bash
python /opt/cronishe/scheduler.py &
python /opt/cronishe/webui.py &
exec your-original-command
```

**Important Notes:**
- Mount a volume for database persistence: `-v ./data:/app/data`
- Expose port 48080 for web UI: `-p 48080:48080`
- Set `DB_PATH` environment variable if needed
- Web UI accessible at `http://localhost:48080` to configure jobs

## Quick Start Guide

1. **Start Cronishe** (using Docker or local method above)

2. **Open the web UI** at http://localhost:48080

3. **Add your first job:**
   - Click "Add New Job"
   - Enter a name (e.g., "Test Job")
   - Enter command (e.g., `python /path/to/script.py` or `echo "Hello World"`)
   - Choose schedule type:
     - **every**: Set interval in minutes
     - **at**: Select days and time
   - Select timezone
   - Click "Add Job"

4. **Monitor execution:**
   - Return to home page to see job status
   - Click "View Runs" to see execution history
   - Click a run ID to view logs

## Example Jobs

### Simple Script (every 5 minutes)
```
Name: Health Check
Path: curl https://example.com/health
Type: every
Interval: 5 minutes
```

### Python Script (daily at 9 AM)
```
Name: Daily Report
Path: python /app/scripts/generate_report.py
Type: at
Days: Mon, Tue, Wed, Thu, Fri
Time: 09:00
Timezone: America/New_York
```

### With Webhooks
```
Name: Backup Job
Path: /usr/local/bin/backup.sh
On Start: https://notify.example.com/start?job=backup
On Success: https://notify.example.com/success?job=backup
On Fail: https://notify.example.com/fail?job=backup
```

## Configuration

### Environment Variables

- `DB_PATH`: Path to SQLite database file (default: `cronishe.db`)

### Docker Compose

Edit `docker-compose.yml` to customize:
- Port mapping (default: `48080:48080`)
- Volume mount (default: `./data:/app/data`)
- Database path (default: `/app/data/cronishe.db`)

## Troubleshooting

**Jobs not running?**
- Check job is active (toggle on home page)
- Verify schedule configuration
- Review scheduler logs for detailed execution info
- Ensure script paths are absolute and accessible

**No log output?**
- Verify script outputs to stdout/stderr
- Use `print()` in Python scripts
- For Python, run with `python -u` to disable buffering

**Webhooks failing?**
- Check URL is accessible from scheduler
- 10-second timeout applies to all webhook calls
- Review scheduler logs for error details

## Documentation

For detailed technical documentation, see `CLAUDE.md` including:
- Complete database schema
- Scheduler logic and algorithms
- Timezone handling details
- API routes
- Development guidelines

## Security Notes

Cronishe is designed for single-user, trusted environments:
- No authentication on web UI
- Jobs execute with `shell=True`
- No input validation on webhook URLs
- Web UI listens on all interfaces (0.0.0.0)

**Recommendation**: Run behind a firewall or use a reverse proxy with authentication for production deployments.

## License

Not specified - add LICENSE file as needed.

## Version

Current version: 0.1.0

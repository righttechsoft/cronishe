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

- **Python 3.13+**: Core runtime with zoneinfo for timezone support
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

**Component Control:**

By default, Docker runs both the scheduler and web UI. You can control which components run using environment variables:

```yaml
# docker-compose.yml - Run only scheduler
environment:
  - RUN_SCHEDULER=true
  - RUN_WEBUI=false
  - RUN_MANAGER=false
```

```yaml
# docker-compose.yml - Run only web UI (read-only, no job execution)
environment:
  - RUN_SCHEDULER=false
  - RUN_WEBUI=true
  - RUN_MANAGER=false
```

```yaml
# docker-compose.yml - Run all components
environment:
  - RUN_SCHEDULER=true
  - RUN_WEBUI=true
  - RUN_MANAGER=true
  - CRONISHE_INSTANCES=Prod:http://prod:48080,Dev:http://dev:48080
  - MANAGER_PORT=48090
```

**Available Components:**
- **Scheduler** (`RUN_SCHEDULER=true`): Job execution engine - runs jobs on schedule
- **Web UI** (`RUN_WEBUI=true`): Management interface at port 48080
- **Manager** (`RUN_MANAGER=true`): Multi-instance dashboard at port 48090 (default: false)

**Common Configurations:**
- **Full instance** (default): `RUN_SCHEDULER=true RUN_WEBUI=true` - Complete Cronishe instance
- **Scheduler only**: `RUN_SCHEDULER=true RUN_WEBUI=false` - Headless job execution
- **UI only**: `RUN_SCHEDULER=false RUN_WEBUI=true` - View-only interface (no execution)
- **Manager only**: `RUN_MANAGER=true RUN_SCHEDULER=false RUN_WEBUI=false` - Monitor multiple instances

### Option 2: Local Development

**Requirements:**
- Python 3.13 or higher
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
    pip install uv && uv pip install --system -r /opt/cronishe/pyproject.toml

# Start Cronishe alongside your application
CMD ["sh", "-c", "python /opt/cronishe/scheduler.py & python /opt/cronishe/webui.py & your-app-command"]
```

#### Method 2: Multi-stage Build

```dockerfile
FROM python:3.13-slim as cronishe
WORKDIR /cronishe
RUN apt-get update && apt-get install -y git && \
    git clone https://github.com/righttechsoft/cronishe.git . && \
    pip install uv && uv pip install --system -r pyproject.toml

FROM python:3.13-slim
# Your existing application setup...
COPY --from=cronishe /cronishe /opt/cronishe
COPY --from=cronishe /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

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

## Multi-Instance Manager

The multi-instance manager allows you to monitor and manage multiple Cronishe instances from a single web interface.

### Features

- Monitor multiple Cronishe instances from one dashboard
- View all jobs from all instances in one place
- Each instance displayed with its own header and job grid
- Real-time job status and last run information
- Direct links to open individual instances
- Error handling for unreachable instances

### Setup

#### 1. Configure Instances

Set the `CRONISHE_INSTANCES` environment variable with your instances in the format:
```
name1:url1,name2:url2,name3:url3
```

**Example:**
```bash
export CRONISHE_INSTANCES="Production:http://prod-server:48080,Staging:http://staging-server:48080,Development:http://localhost:48080"
```

#### 2. Run the Manager

```bash
python manager.py
```

By default, the manager runs on port **48090**. You can customize this with the `MANAGER_PORT` environment variable:

```bash
export MANAGER_PORT=8080
python manager.py
```

#### 3. Access the Dashboard

Open your browser to:
```
http://localhost:48090
```

### Manager Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CRONISHE_INSTANCES` | Comma-separated list of instances | `Local:http://localhost:48080` | `Prod:http://server1:48080,Dev:http://localhost:48080` |
| `MANAGER_PORT` | Port for manager web interface | `48090` | `8080` |

### Docker Setup with Manager

**docker-compose.yml Example:**

```yaml
version: '3.8'

services:
  # Cronishe Instance 1 - Production
  cronishe-prod:
    build: .
    ports:
      - "48080:48080"
    volumes:
      - ./data-prod:/app/data
    environment:
      - DB_PATH=/app/data/cronishe.db

  # Cronishe Instance 2 - Staging
  cronishe-staging:
    build: .
    ports:
      - "48081:48080"
    volumes:
      - ./data-staging:/app/data
    environment:
      - DB_PATH=/app/data/cronishe.db

  # Multi-Instance Manager
  cronishe-manager:
    build: .
    command: python manager.py
    ports:
      - "48090:48090"
    environment:
      - CRONISHE_INSTANCES=Production:http://cronishe-prod:48080,Staging:http://cronishe-staging:48080
      - MANAGER_PORT=48090
    depends_on:
      - cronishe-prod
      - cronishe-staging
```

### Manager API Endpoints

The manager requires each Cronishe instance to expose the following JSON API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs` | GET | List all jobs |
| `/api/job/<id>` | GET | Get single job details |
| `/api/job/<id>/runs` | GET | Get job run history |

These endpoints are automatically available in `webui.py`.

### Manager Features by Instance

Each instance section shows:
- **Instance Name** - Configured name (e.g., "Production", "Staging")
- **Instance URL** - HTTP endpoint for the instance
- **Job Grid** - All jobs with:
  - Job ID
  - Job Name
  - Command/Path
  - Schedule (human-readable)
  - Timezone
  - Status (Active/Inactive)
  - Last Run (converted to browser timezone)
  - Last Result (Success/Failed)
- **Open Instance Button** - Direct link to full instance interface

### Manager Error Handling

If an instance is unreachable:
- Error message displayed instead of job grid
- Shows which URL failed to connect
- Other instances continue to display normally
- Manager continues to function

### Manager Use Cases

**Multi-Environment Setup**
Monitor production, staging, and development instances side-by-side:
```bash
export CRONISHE_INSTANCES="Prod:http://prod:48080,Staging:http://staging:48080,Dev:http://localhost:48080"
```

**Multi-Server Setup**
Monitor multiple production servers from one dashboard:
```bash
export CRONISHE_INSTANCES="Server1:http://server1:48080,Server2:http://server2:48080,Server3:http://server3:48080"
```

**Multi-Tenant Setup**
Monitor different client instances:
```bash
export CRONISHE_INSTANCES="Client-A:http://client-a:48080,Client-B:http://client-b:48080"
```

### Manager Capabilities

- **Add Jobs**: Create new jobs on any instance with full schedule configuration
- **Edit Jobs**: Modify existing job schedules, paths, webhooks, and settings
- **Enable/Disable Jobs**: Toggle job active status from the manager
- **Delete Jobs**: Remove jobs from instances with confirmation dialog
- **Monitor Status**: Real-time job status, schedule, and last run information
- **Modal Forms**: User-friendly modal interface for all job operations
- **Schedule Types**: Support for both "every N minutes" and "at specific time" schedules
- **Timezone Support**: Configure job-specific timezones

### Manager Limitations

- **Timeout**: 5-second timeout per instance request
- **No Authentication**: Manager has no built-in authentication
- **Polling**: Manual refresh required (no auto-refresh yet)

### Manager Future Enhancements

Planned features:
- Auto-refresh with configurable interval
- Aggregated statistics across all instances
- Real-time notifications for failures
- Search/filter across all instances
- Authentication and access control
- WebSocket support for real-time updates
- Bulk operations (enable/disable/delete multiple jobs)

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

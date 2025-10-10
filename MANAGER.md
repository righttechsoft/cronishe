# Cronishe Multi-Instance Manager

The multi-instance manager allows you to monitor and manage multiple Cronishe instances from a single web interface.

## Features

- Monitor multiple Cronishe instances from one dashboard
- View all jobs from all instances in one place
- Each instance displayed with its own header and job grid
- Real-time job status and last run information
- Direct links to open individual instances
- Error handling for unreachable instances

## Setup

### 1. Configure Instances

Set the `CRONISHE_INSTANCES` environment variable with your instances in the format:
```
name1:url1,name2:url2,name3:url3
```

**Example:**
```bash
export CRONISHE_INSTANCES="Production:http://prod-server:48080,Staging:http://staging-server:48080,Development:http://localhost:48080"
```

### 2. Run the Manager

```bash
python manager.py
```

By default, the manager runs on port **48090**. You can customize this with the `MANAGER_PORT` environment variable:

```bash
export MANAGER_PORT=8080
python manager.py
```

### 3. Access the Dashboard

Open your browser to:
```
http://localhost:48090
```

## Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CRONISHE_INSTANCES` | Comma-separated list of instances | `Local:http://localhost:48080` | `Prod:http://server1:48080,Dev:http://localhost:48080` |
| `MANAGER_PORT` | Port for manager web interface | `48090` | `8080` |

## Docker Setup

### docker-compose.yml Example

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

## API Endpoints

The manager requires each Cronishe instance to expose the following JSON API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs` | GET | List all jobs |
| `/api/job/<id>` | GET | Get single job details |
| `/api/job/<id>/runs` | GET | Get job run history |

These endpoints are automatically available in the updated `webui.py`.

## Features by Instance

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

## Error Handling

If an instance is unreachable:
- Error message displayed instead of job grid
- Shows which URL failed to connect
- Other instances continue to display normally
- Manager continues to function

## Use Cases

### Multi-Environment Setup
Monitor production, staging, and development instances side-by-side:
```bash
export CRONISHE_INSTANCES="Prod:http://prod:48080,Staging:http://staging:48080,Dev:http://localhost:48080"
```

### Multi-Server Setup
Monitor multiple production servers from one dashboard:
```bash
export CRONISHE_INSTANCES="Server1:http://server1:48080,Server2:http://server2:48080,Server3:http://server3:48080"
```

### Multi-Tenant Setup
Monitor different client instances:
```bash
export CRONISHE_INSTANCES="Client-A:http://client-a:48080,Client-B:http://client-b:48080"
```

## Limitations

- **Read-only**: Manager is currently view-only (no editing/creating jobs)
- **Timeout**: 5-second timeout per instance request
- **No Authentication**: Manager has no built-in authentication
- **Polling**: Manual refresh required (no auto-refresh yet)

## Future Enhancements

Planned features:
- Auto-refresh with configurable interval
- Job creation/editing from manager
- Aggregated statistics across all instances
- Real-time notifications for failures
- Search/filter across all instances
- Authentication and access control
- WebSocket support for real-time updates

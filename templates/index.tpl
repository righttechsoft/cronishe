<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cronishe - Job Scheduler</title>
    <link rel="apple-touch-icon" sizes="180x180" href="/static/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/favicon-16x16.png">
    <link rel="manifest" href="/static/site.webmanifest">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .header {
            background: #2c3e50;
            color: white;
            padding: 20px 30px;
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            font-size: 24px;
            font-weight: 600;
        }

        .header-content {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .logo {
            height: 40px;
            width: auto;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
            display: inline-block;
            transition: all 0.2s;
        }

        .btn-primary {
            background: #3498db;
            color: white;
        }

        .btn-primary:hover {
            background: #2980b9;
        }

        .btn-success {
            background: #27ae60;
            color: white;
        }

        .btn-success:hover {
            background: #229954;
        }

        .btn-warning {
            background: #f39c12;
            color: white;
        }

        .btn-warning:hover {
            background: #e67e22;
        }

        .btn-danger {
            background: #e74c3c;
            color: white;
        }

        .btn-danger:hover {
            background: #c0392b;
        }

        .btn-secondary {
            background: #95a5a6;
            color: white;
        }

        .btn-secondary:hover {
            background: #7f8c8d;
        }

        .btn-sm {
            padding: 6px 12px;
            font-size: 12px;
        }

        .content {
            padding: 30px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th {
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }

        tr:hover {
            background: #f8f9fa;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-active {
            background: #d4edda;
            color: #155724;
        }

        .status-inactive {
            background: #f8d7da;
            color: #721c24;
        }

        .result-success {
            color: #27ae60;
            font-weight: 600;
        }

        .result-fail {
            color: #e74c3c;
            font-weight: 600;
        }

        .actions {
            display: flex;
            gap: 5px;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #7f8c8d;
        }

        .empty-state h2 {
            font-size: 20px;
            margin-bottom: 10px;
        }

        .empty-state p {
            font-size: 14px;
            margin-bottom: 20px;
        }

        .timezone-info {
            font-size: 12px;
            color: #ecf0f1;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <img src="/static/logo.png" alt="Cronishe" class="logo">
                <div>
                    <h1>Cronishe - Job Scheduler</h1>
                    <div class="timezone-info">Showing times in: <span id="browser-timezone">Loading...</span></div>
                </div>
            </div>
            <a href="/job/add" class="btn btn-primary">+ Add Job</a>
        </div>

        <div class="content">
            % if len(jobs) == 0:
                <div class="empty-state">
                    <h2>No jobs scheduled</h2>
                    <p>Get started by adding your first job</p>
                    <a href="/job/add" class="btn btn-primary">+ Add Job</a>
                </div>
            % else:
                <table>
                    <thead>
                        <tr>
                            <th style="width: 200px;">Name</th>
                            <th>Path</th>
                            <th>Schedule</th>
                            <th>Timezone</th>
                            <th style="width: 100px;">Status</th>
                            <th>Last Run</th>
                            <th style="width: 80px;">Result</th>
                            <th style="width: 90px;">Duration</th>
                            <th style="width: 280px;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for job in jobs:
                        <tr>
                            <td style="word-wrap: break-word; white-space: normal;"><strong>{{job['name']}}</strong></td>
                            <td><code>{{job['path']}}</code></td>
                            <td>{{job['schedule_text']}}</td>
                            <td>{{job.get('timezone') or 'UTC'}}</td>
                            <td>
                                % if job['active']:
                                    <span class="status-badge status-active">Active</span>
                                % else:
                                    <span class="status-badge status-inactive">Inactive</span>
                                % end
                            </td>
                            <td>
                                % if job.get('last_run_utc'):
                                    <span class="utc-time" data-utc="{{job['last_run_utc']}}">{{job['last_run_utc']}}</span>
                                % else:
                                    Never
                                % end
                            </td>
                            <td>
                                % if job['last_run_result'] == 'success':
                                    <span class="result-success">Success</span>
                                % elif job['last_run_result'] == 'fail':
                                    <span class="result-fail">Failed</span>
                                % else:
                                    <span>-</span>
                                % end
                            </td>
                            <td>
                                <code>{{job.get('last_duration', '-')}}</code>
                            </td>
                            <td>
                                <div class="actions">
                                    <button class="btn btn-success btn-sm" onclick="runJobNow({{job['id']}}, '{{job['name']}}')">Run Now</button>
                                    <a href="/job/{{job['id']}}/runs" class="btn btn-secondary btn-sm">Runs</a>
                                    <a href="/job/{{job['id']}}/edit" class="btn btn-primary btn-sm">Edit</a>
                                    % if job['active']:
                                        <a href="/job/{{job['id']}}/toggle" class="btn btn-warning btn-sm">Disable</a>
                                    % else:
                                        <a href="/job/{{job['id']}}/toggle" class="btn btn-success btn-sm">Enable</a>
                                    % end
                                    <form method="POST" action="/job/{{job['id']}}/delete" style="display: inline;" onsubmit="return confirm('Are you sure you want to delete this job?');">
                                        <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                                    </form>
                                </div>
                            </td>
                        </tr>
                        % end
                    </tbody>
                </table>
            % end
        </div>
    </div>

    <script>
        // Get browser timezone
        const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        document.getElementById('browser-timezone').textContent = browserTimezone;

        // Convert all UTC timestamps to local time
        function formatLocalTime(utcTimestamp) {
            if (!utcTimestamp) return 'Never';

            // Parse UTC timestamp (add 'Z' if not present to indicate UTC)
            const utcStr = utcTimestamp.endsWith('Z') ? utcTimestamp : utcTimestamp + 'Z';
            const date = new Date(utcStr);

            // Format as local time
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');

            return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        }

        // Convert all elements with class 'utc-time'
        document.addEventListener('DOMContentLoaded', function() {
            const timeElements = document.querySelectorAll('.utc-time');
            timeElements.forEach(function(el) {
                const utcTime = el.getAttribute('data-utc');
                if (utcTime) {
                    el.textContent = formatLocalTime(utcTime);
                }
            });
        });

        // Run job now
        async function runJobNow(jobId, jobName) {
            if (!confirm(`Run job "${jobName}" now?`)) {
                return;
            }

            try {
                const response = await fetch(`/api/job/${jobId}/run`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (!response.ok) {
                    alert('Failed to run job: ' + (data.error || 'Unknown error'));
                    return;
                }

                alert('Job started successfully!');
                // Reload page to show updated state
                setTimeout(() => location.reload(), 1000);
            } catch (error) {
                alert('Failed to run job: ' + error.message);
            }
        }
    </script>
</body>
</html>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cronishe - Multi-Instance Manager</title>
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

        .main-header {
            max-width: 1400px;
            margin: 0 auto 30px;
            background: #2c3e50;
            color: white;
            padding: 20px 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .main-header h1 {
            font-size: 28px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .logo {
            height: 45px;
            width: auto;
        }

        .timezone-info {
            font-size: 12px;
            color: #ecf0f1;
            margin-top: 8px;
        }

        .instance-container {
            max-width: 1400px;
            margin: 0 auto 30px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .instance-header {
            background: #34495e;
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .instance-header h2 {
            font-size: 20px;
            font-weight: 600;
        }

        .instance-url {
            font-size: 13px;
            color: #bdc3c7;
            font-family: 'Courier New', monospace;
        }

        .content {
            padding: 30px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
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

        .btn {
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
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

        .btn-secondary {
            background: #95a5a6;
            color: white;
        }

        .btn-secondary:hover {
            background: #7f8c8d;
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #7f8c8d;
        }

        .empty-state h3 {
            font-size: 16px;
            margin-bottom: 8px;
        }

        .error-state {
            text-align: center;
            padding: 40px 20px;
            color: #e74c3c;
            background: #fadbd8;
            border-radius: 4px;
        }

        .error-state h3 {
            font-size: 16px;
            margin-bottom: 8px;
        }

        code {
            background: #34495e;
            color: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <div class="main-header">
        <div>
            <h1>
                <img src="/static/logo.png" alt="Cronishe" class="logo">
                Cronishe - Multi-Instance Manager
            </h1>
            <div class="timezone-info">Showing times in: <span id="browser-timezone">Loading...</span></div>
        </div>
    </div>

    % for instance in instances:
    <div class="instance-container">
        <div class="instance-header">
            <div>
                <h2>{{instance['name']}}</h2>
                <div class="instance-url">{{instance['url']}}</div>
            </div>
            <a href="{{instance['url']}}" target="_blank" class="btn btn-primary">Open Instance</a>
        </div>

        <div class="content">
            % if instance['error']:
                <div class="error-state">
                    <h3>⚠ Unable to connect to instance</h3>
                    <p>Failed to fetch jobs from <code>{{instance['url']}}</code></p>
                    <p style="margin-top: 10px; font-size: 13px;">Check that the instance is running and accessible.</p>
                </div>
            % elif len(instance['jobs']) == 0:
                <div class="empty-state">
                    <h3>No jobs scheduled</h3>
                    <p>This instance has no jobs configured</p>
                </div>
            % else:
                <table>
                    <thead>
                        <tr>
                            <th style="width: 50px;">ID</th>
                            <th>Name</th>
                            <th>Path</th>
                            <th>Schedule</th>
                            <th>Timezone</th>
                            <th style="width: 100px;">Status</th>
                            <th>Last Run</th>
                            <th style="width: 80px;">Result</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for job in instance['jobs']:
                        <tr>
                            <td>{{job['id']}}</td>
                            <td><strong>{{job['name']}}</strong></td>
                            <td><code style="background: #ecf0f1; color: #2c3e50;">{{job['path']}}</code></td>
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
                                % if job.get('last_run'):
                                    <span class="utc-time" data-utc="{{job['last_run']}}">{{job['last_run']}}</span>
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
                        </tr>
                        % end
                    </tbody>
                </table>
            % end
        </div>
    </div>
    % end

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
    </script>
</body>
</html>

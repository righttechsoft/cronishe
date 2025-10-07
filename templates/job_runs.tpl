<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Runs - Cronishe</title>
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
            max-width: 1200px;
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

        .btn-secondary {
            background: #95a5a6;
            color: white;
        }

        .btn-secondary:hover {
            background: #7f8c8d;
        }

        .btn-primary {
            background: #3498db;
            color: white;
        }

        .btn-primary:hover {
            background: #2980b9;
        }

        .btn-sm {
            padding: 6px 12px;
            font-size: 12px;
        }

        .content {
            padding: 30px;
        }

        .job-info {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }

        .job-info h2 {
            font-size: 18px;
            margin-bottom: 10px;
        }

        .job-info p {
            font-size: 14px;
            color: #555;
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

        .result-success {
            color: #27ae60;
            font-weight: 600;
        }

        .result-fail {
            color: #e74c3c;
            font-weight: 600;
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
                    <h1>Job Runs: {{job['name']}}</h1>
                    <div class="timezone-info">Showing times in: <span id="browser-timezone">Loading...</span></div>
                </div>
            </div>
            <a href="/" class="btn btn-secondary">Back to Jobs</a>
        </div>

        <div class="content">
            <div class="job-info">
                <h2>Job Details</h2>
                <p><strong>Path:</strong> <code>{{job['path']}}</code></p>
            </div>

            % if len(runs) == 0:
                <div class="empty-state">
                    <h2>No runs yet</h2>
                    <p>This job hasn't been executed yet</p>
                </div>
            % else:
                <table>
                    <thead>
                        <tr>
                            <th style="width: 60px;">Run ID</th>
                            <th>Started</th>
                            <th>Finished</th>
                            <th style="width: 100px;">Duration</th>
                            <th style="width: 100px;">Result</th>
                            <th style="width: 100px;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for run in runs:
                        <tr>
                            <td>{{run['id']}}</td>
                            <td>
                                % if run.get('start_at_utc'):
                                    <span class="utc-time" data-utc="{{run['start_at_utc']}}">{{run['start_at_utc']}}</span>
                                % else:
                                    -
                                % end
                            </td>
                            <td>
                                % if run.get('finish_at_utc'):
                                    <span class="utc-time" data-utc="{{run['finish_at_utc']}}">{{run['finish_at_utc']}}</span>
                                % else:
                                    Running
                                % end
                            </td>
                            <td>{{run.get('duration', '-')}}</td>
                            <td>
                                % if run['result'] == 'success':
                                    <span class="result-success">Success</span>
                                % elif run['result'] == 'fail':
                                    <span class="result-fail">Failed</span>
                                % else:
                                    <span>Running</span>
                                % end
                            </td>
                            <td>
                                <a href="/run/{{run['id']}}/logs" class="btn btn-primary btn-sm">View Logs</a>
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
            if (!utcTimestamp) return '-';

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

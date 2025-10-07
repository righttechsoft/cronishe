<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Run Logs - Cronishe</title>
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

        .content {
            padding: 30px;
        }

        .run-info {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }

        .run-info h2 {
            font-size: 18px;
            margin-bottom: 10px;
        }

        .run-info p {
            font-size: 14px;
            color: #555;
            margin-bottom: 5px;
        }

        .result-success {
            color: #27ae60;
            font-weight: 600;
        }

        .result-fail {
            color: #e74c3c;
            font-weight: 600;
        }

        .log-container {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
            max-height: 600px;
            overflow-y: auto;
        }

        .log-line {
            margin-bottom: 2px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .log-timestamp {
            color: #858585;
            margin-right: 10px;
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

        code {
            background: #34495e;
            color: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
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
                    <h1>Run Logs: {{run['job_name']}} - Run #{{run['id']}}</h1>
                    <div class="timezone-info">Showing times in: <span id="browser-timezone">Loading...</span></div>
                </div>
            </div>
            <a href="/job/{{run['job_id']}}/runs" class="btn btn-secondary">Back to Runs</a>
        </div>

        <div class="content">
            <div class="run-info">
                <h2>Run Information</h2>
                <p><strong>Started:</strong>
                    % if run.get('start_at_utc'):
                        <span class="utc-time" data-utc="{{run['start_at_utc']}}">{{run['start_at_utc']}}</span>
                    % else:
                        -
                    % end
                </p>
                <p><strong>Finished:</strong>
                    % if run.get('finish_at_utc'):
                        <span class="utc-time" data-utc="{{run['finish_at_utc']}}">{{run['finish_at_utc']}}</span>
                    % else:
                        Running
                    % end
                </p>
                <p><strong>Result:</strong>
                    % if run['result'] == 'success':
                        <span class="result-success">Success</span>
                    % elif run['result'] == 'fail':
                        <span class="result-fail">Failed</span>
                    % else:
                        <span>Running</span>
                    % end
                </p>
            </div>

            <h3 style="margin-bottom: 10px;">Output</h3>

            % if len(logs) == 0:
                <div class="empty-state">
                    <h2>No output</h2>
                    <p>This job run didn't produce any output</p>
                </div>
            % else:
                <div class="log-container">
                    % for log in logs:
                    <div class="log-line">
                        % if log.get('timestamp_utc'):
                            <span class="log-timestamp utc-time-short" data-utc="{{log['timestamp_utc']}}">{{log['timestamp_utc']}}</span>
                        % end
                        {{log['log_line']}}
                    </div>
                    % end
                </div>
            % end
        </div>
    </div>

    <script>
        // Get browser timezone
        const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        document.getElementById('browser-timezone').textContent = browserTimezone;

        // Convert full UTC timestamps to local time
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

        // Convert UTC timestamps to local time (short format for logs)
        function formatLocalTimeShort(utcTimestamp) {
            if (!utcTimestamp) return '';

            // Parse UTC timestamp (add 'Z' if not present to indicate UTC)
            const utcStr = utcTimestamp.endsWith('Z') ? utcTimestamp : utcTimestamp + 'Z';
            const date = new Date(utcStr);

            // Format as local time (short format)
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');
            const ms = String(date.getMilliseconds()).padStart(3, '0');

            return `${hours}:${minutes}:${seconds}.${ms}`;
        }

        // Convert all elements with class 'utc-time'
        document.addEventListener('DOMContentLoaded', function() {
            // Full timestamps
            const timeElements = document.querySelectorAll('.utc-time');
            timeElements.forEach(function(el) {
                const utcTime = el.getAttribute('data-utc');
                if (utcTime) {
                    el.textContent = formatLocalTime(utcTime);
                }
            });

            // Short timestamps (for logs)
            const shortTimeElements = document.querySelectorAll('.utc-time-short');
            shortTimeElements.forEach(function(el) {
                const utcTime = el.getAttribute('data-utc');
                if (utcTime) {
                    el.textContent = formatLocalTimeShort(utcTime);
                }
            });
        });
    </script>
</body>
</html>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add Job - Cronishe</title>
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
            max-width: 800px;
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

        .content {
            padding: 30px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            font-size: 14px;
        }

        input[type="text"],
        input[type="number"],
        select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }

        input[type="text"]:focus,
        input[type="number"]:focus,
        select:focus {
            outline: none;
            border-color: #3498db;
        }

        .checkbox-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .checkbox-item input[type="checkbox"] {
            width: auto;
        }

        .schedule-options {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 20px;
            margin-top: 10px;
            display: none;
        }

        .schedule-options.active {
            display: block;
        }

        .time-inputs {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .time-inputs input {
            width: 80px;
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

        .btn-secondary {
            background: #95a5a6;
            color: white;
        }

        .btn-secondary:hover {
            background: #7f8c8d;
        }

        .form-actions {
            display: flex;
            gap: 10px;
            margin-top: 30px;
        }

        .help-text {
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 5px;
        }

        code {
            background: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <img src="/static/logo.png" alt="Cronishe" class="logo">
                <h1>Add Job</h1>
            </div>
        </div>

        <div class="content">
            <form method="POST" action="/job/add">
                <div class="form-group">
                    <label for="name">Job Name</label>
                    <input type="text" id="name" name="name" required>
                </div>

                <div class="form-group">
                    <label for="path">Command / Script Path</label>
                    <input type="text" id="path" name="path" required>
                    <div class="help-text">Example: <code>python /path/to/script.py</code> or <code>/path/to/executable.sh</code></div>
                </div>

                <div class="form-group">
                    <label for="frequency_type">Schedule Type</label>
                    <select id="frequency_type" name="frequency_type" onchange="toggleScheduleType()" required>
                        <option value="every">Run Every (Interval)</option>
                        <option value="at">Run At (Specific Time)</option>
                    </select>
                </div>

                <div id="schedule_every" class="schedule-options active">
                    <div class="form-group">
                        <label for="frequency_every_min">Interval (minutes)</label>
                        <input type="number" id="frequency_every_min" name="frequency_every_min" min="1" value="30">
                        <div class="help-text">Job will run every N minutes</div>
                    </div>
                </div>

                <div id="schedule_at" class="schedule-options">
                    <div class="form-group">
                        <label>Days of Week</label>
                        <div class="checkbox-group">
                            <div class="checkbox-item">
                                <input type="checkbox" id="day_mon" name="day_mon" value="1">
                                <label for="day_mon" style="margin: 0;">Monday</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="day_tue" name="day_tue" value="1">
                                <label for="day_tue" style="margin: 0;">Tuesday</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="day_wed" name="day_wed" value="1">
                                <label for="day_wed" style="margin: 0;">Wednesday</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="day_thu" name="day_thu" value="1">
                                <label for="day_thu" style="margin: 0;">Thursday</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="day_fri" name="day_fri" value="1">
                                <label for="day_fri" style="margin: 0;">Friday</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="day_sat" name="day_sat" value="1">
                                <label for="day_sat" style="margin: 0;">Saturday</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="day_sun" name="day_sun" value="1">
                                <label for="day_sun" style="margin: 0;">Sunday</label>
                            </div>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Time</label>
                        <div class="time-inputs">
                            <input type="number" name="frequency_at_hr" min="0" max="23" value="9" placeholder="HH"> :
                            <input type="number" name="frequency_at_min" min="0" max="59" value="0" placeholder="MM">
                        </div>
                        <div class="help-text">24-hour format (e.g., 14:30 for 2:30 PM)</div>
                    </div>
                </div>

                <div class="form-group">
                    <label for="timezone">Timezone</label>
                    <input type="text" id="timezone" name="timezone" value="UTC">
                    <div class="help-text">Examples: <code>UTC</code>, <code>America/New_York</code>, <code>Europe/London</code>, <code>Asia/Tokyo</code></div>
                </div>

                <div class="form-group">
                    <label for="on_start">On Start Webhook (optional)</label>
                    <input type="text" id="on_start" name="on_start" placeholder="https://example.com/webhook/start">
                </div>

                <div class="form-group">
                    <label for="on_success">On Success Webhook (optional)</label>
                    <input type="text" id="on_success" name="on_success" placeholder="https://example.com/webhook/success">
                </div>

                <div class="form-group">
                    <label for="on_fail">On Failure Webhook (optional)</label>
                    <input type="text" id="on_fail" name="on_fail" placeholder="https://example.com/webhook/fail">
                </div>

                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">Create Job</button>
                    <a href="/" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
    </div>

    <script>
        function toggleScheduleType() {
            const type = document.getElementById('frequency_type').value;
            const everySection = document.getElementById('schedule_every');
            const atSection = document.getElementById('schedule_at');

            if (type === 'every') {
                everySection.classList.add('active');
                atSection.classList.remove('active');
            } else {
                everySection.classList.remove('active');
                atSection.classList.add('active');
            }
        }
    </script>
</body>
</html>

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

        .btn-toggle {
            background: #f39c12;
            color: white;
        }

        .btn-toggle:hover {
            background: #e67e22;
        }

        .btn-delete {
            background: #e74c3c;
            color: white;
        }

        .btn-delete:hover {
            background: #c0392b;
        }

        .actions {
            display: flex;
            gap: 5px;
        }

        .btn-edit {
            background: #3498db;
            color: white;
        }

        .btn-edit:hover {
            background: #2980b9;
        }

        .btn-success {
            background: #27ae60;
            color: white;
        }

        .btn-success:hover {
            background: #229954;
        }

        /* Modal styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            overflow: auto;
        }

        .modal-content {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 0;
            border-radius: 8px;
            width: 600px;
            max-width: 90%;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }

        .modal-header {
            padding: 20px 30px;
            background: #34495e;
            color: white;
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h2 {
            margin: 0;
            font-size: 20px;
        }

        .modal-close {
            color: white;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            background: none;
            border: none;
            padding: 0;
            width: 30px;
            height: 30px;
            line-height: 1;
        }

        .modal-close:hover {
            color: #e74c3c;
        }

        .modal-body {
            padding: 30px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #2c3e50;
        }

        .form-group input[type="text"],
        .form-group input[type="number"],
        .form-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 14px;
        }

        .form-group input[type="text"]:focus,
        .form-group input[type="number"]:focus,
        .form-group select:focus {
            outline: none;
            border-color: #3498db;
        }

        .form-row {
            display: flex;
            gap: 10px;
        }

        .form-row .form-group {
            flex: 1;
        }

        .checkbox-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .checkbox-group label {
            display: flex;
            align-items: center;
            gap: 5px;
            font-weight: normal;
        }

        .checkbox-group input[type="checkbox"] {
            width: auto;
            margin: 0;
        }

        .modal-footer {
            padding: 20px 30px;
            background: #ecf0f1;
            border-radius: 0 0 8px 8px;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }

        .schedule-section {
            padding: 15px;
            background: #ecf0f1;
            border-radius: 4px;
            margin-bottom: 20px;
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
            <div style="display: flex; gap: 10px;">
                % if not instance['error']:
                <button class="btn btn-success" onclick="showAddJobModal('{{instance['url']}}', '{{instance['name']}}')">Add Job</button>
                % end
                <a href="{{instance['url']}}" target="_blank" class="btn btn-primary">Open Instance</a>
            </div>
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
                            <th style="width: 240px;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for job in instance['jobs']:
                        <tr id="job-{{instance['url']}}-{{job['id']}}">
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
                            <td>
                                <div class="actions">
                                    <button class="btn btn-edit" onclick='showEditJobModal({{!repr(job)}}, "{{instance['url']}}")'>Edit</button>
                                    <button class="btn btn-toggle" onclick="toggleJob('{{instance['url']}}', {{job['id']}})">
                                        % if job['active']:
                                            Disable
                                        % else:
                                            Enable
                                        % end
                                    </button>
                                    <button class="btn btn-delete" onclick="deleteJob('{{instance['url']}}', {{job['id']}}, '{{job['name']}}')">Delete</button>
                                </div>
                            </td>
                        </tr>
                        % end
                    </tbody>
                </table>
            % end
        </div>
    </div>
    % end

    <!-- Job Modal -->
    <div id="jobModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Add Job</h2>
                <button class="modal-close" onclick="closeJobModal()">&times;</button>
            </div>
            <div class="modal-body">
                <form id="jobForm">
                    <div class="form-group">
                        <label for="jobName">Job Name *</label>
                        <input type="text" id="jobName" required>
                    </div>

                    <div class="form-group">
                        <label for="jobPath">Command/Script Path *</label>
                        <input type="text" id="jobPath" required placeholder="e.g., python /path/to/script.py">
                    </div>

                    <div class="schedule-section">
                        <div class="form-group">
                            <label for="frequencyType">Schedule Type *</label>
                            <select id="frequencyType" onchange="toggleScheduleType()">
                                <option value="every">Every N Minutes</option>
                                <option value="at">At Specific Time</option>
                            </select>
                        </div>

                        <div id="everySection">
                            <div class="form-group">
                                <label for="frequencyEveryMin">Run Every (minutes) *</label>
                                <input type="number" id="frequencyEveryMin" min="1" value="60">
                            </div>
                        </div>

                        <div id="atSection" style="display: none;">
                            <div class="form-group">
                                <label>Days of Week *</label>
                                <div class="checkbox-group">
                                    <label><input type="checkbox" id="dayMon"> Monday</label>
                                    <label><input type="checkbox" id="dayTue"> Tuesday</label>
                                    <label><input type="checkbox" id="dayWed"> Wednesday</label>
                                    <label><input type="checkbox" id="dayThu"> Thursday</label>
                                    <label><input type="checkbox" id="dayFri"> Friday</label>
                                    <label><input type="checkbox" id="daySat"> Saturday</label>
                                    <label><input type="checkbox" id="daySun"> Sunday</label>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="frequencyAtHr">Hour (0-23) *</label>
                                    <input type="number" id="frequencyAtHr" min="0" max="23" value="9">
                                </div>
                                <div class="form-group">
                                    <label for="frequencyAtMin">Minute (0-59) *</label>
                                    <input type="number" id="frequencyAtMin" min="0" max="59" value="0">
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="jobTimezone">Timezone</label>
                        <select id="jobTimezone">
                            <option value="UTC">UTC</option>
                            <option value="America/New_York">America/New_York</option>
                            <option value="America/Chicago">America/Chicago</option>
                            <option value="America/Los_Angeles">America/Los_Angeles</option>
                            <option value="Europe/London">Europe/London</option>
                            <option value="Europe/Paris">Europe/Paris</option>
                            <option value="Asia/Tokyo">Asia/Tokyo</option>
                            <option value="Australia/Sydney">Australia/Sydney</option>
                            <option value="Pacific/Auckland">Pacific/Auckland</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="onStart">Webhook: On Start</label>
                        <input type="text" id="onStart" placeholder="https://example.com/webhook/start">
                    </div>

                    <div class="form-group">
                        <label for="onSuccess">Webhook: On Success</label>
                        <input type="text" id="onSuccess" placeholder="https://example.com/webhook/success">
                    </div>

                    <div class="form-group">
                        <label for="onFail">Webhook: On Fail</label>
                        <input type="text" id="onFail" placeholder="https://example.com/webhook/fail">
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeJobModal()">Cancel</button>
                <button class="btn btn-primary" onclick="saveJob()">Save Job</button>
            </div>
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

        // Toggle job active/inactive
        async function toggleJob(instanceUrl, jobId) {
            try {
                const response = await fetch('/proxy/toggle', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        instance_url: instanceUrl,
                        job_id: jobId
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    alert('Failed to toggle job: ' + (error.error || 'Unknown error'));
                    return;
                }

                // Reload page to show updated state
                location.reload();
            } catch (error) {
                alert('Failed to toggle job: ' + error.message);
            }
        }

        // Delete job
        async function deleteJob(instanceUrl, jobId, jobName) {
            if (!confirm(`Are you sure you want to delete job "${jobName}"? This cannot be undone.`)) {
                return;
            }

            try {
                const response = await fetch('/proxy/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        instance_url: instanceUrl,
                        job_id: jobId
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    alert('Failed to delete job: ' + (error.error || 'Unknown error'));
                    return;
                }

                // Reload page to show updated state
                location.reload();
            } catch (error) {
                alert('Failed to delete job: ' + error.message);
            }
        }

        // Modal state
        let currentInstance = null;
        let currentJobId = null;
        let isEditMode = false;

        // Toggle schedule type
        function toggleScheduleType() {
            const type = document.getElementById('frequencyType').value;
            const everySection = document.getElementById('everySection');
            const atSection = document.getElementById('atSection');

            if (type === 'every') {
                everySection.style.display = 'block';
                atSection.style.display = 'none';
            } else {
                everySection.style.display = 'none';
                atSection.style.display = 'block';
            }
        }

        // Show add job modal
        function showAddJobModal(instanceUrl, instanceName) {
            currentInstance = instanceUrl;
            currentJobId = null;
            isEditMode = false;

            document.getElementById('modalTitle').textContent = `Add Job - ${instanceName}`;
            document.getElementById('jobForm').reset();
            document.getElementById('frequencyType').value = 'every';
            toggleScheduleType();

            document.getElementById('jobModal').style.display = 'block';
        }

        // Show edit job modal
        function showEditJobModal(job, instanceUrl) {
            currentInstance = instanceUrl;
            currentJobId = job.id;
            isEditMode = true;

            document.getElementById('modalTitle').textContent = `Edit Job - ${job.name}`;

            // Fill form
            document.getElementById('jobName').value = job.name;
            document.getElementById('jobPath').value = job.path;
            document.getElementById('frequencyType').value = job.frequency_type;

            if (job.frequency_type === 'every') {
                document.getElementById('frequencyEveryMin').value = job.frequency_every_min || 60;
            } else {
                document.getElementById('dayMon').checked = job.frequency_at_mon === 1;
                document.getElementById('dayTue').checked = job.frequency_at_tue === 1;
                document.getElementById('dayWed').checked = job.frequency_at_wed === 1;
                document.getElementById('dayThu').checked = job.frequency_at_thu === 1;
                document.getElementById('dayFri').checked = job.frequency_at_fri === 1;
                document.getElementById('daySat').checked = job.frequency_at_sat === 1;
                document.getElementById('daySun').checked = job.frequency_at_sun === 1;
                document.getElementById('frequencyAtHr').value = job.frequency_at_hr || 9;
                document.getElementById('frequencyAtMin').value = job.frequency_at_min || 0;
            }

            document.getElementById('jobTimezone').value = job.timezone || 'UTC';
            document.getElementById('onStart').value = job.on_start || '';
            document.getElementById('onSuccess').value = job.on_success || '';
            document.getElementById('onFail').value = job.on_fail || '';

            toggleScheduleType();
            document.getElementById('jobModal').style.display = 'block';
        }

        // Close modal
        function closeJobModal() {
            document.getElementById('jobModal').style.display = 'none';
        }

        // Close modal on outside click
        window.onclick = function(event) {
            const modal = document.getElementById('jobModal');
            if (event.target === modal) {
                closeJobModal();
            }
        }

        // Save job (create or update)
        async function saveJob() {
            const jobData = {
                name: document.getElementById('jobName').value,
                path: document.getElementById('jobPath').value,
                frequency_type: document.getElementById('frequencyType').value,
                timezone: document.getElementById('jobTimezone').value,
                on_start: document.getElementById('onStart').value || null,
                on_success: document.getElementById('onSuccess').value || null,
                on_fail: document.getElementById('onFail').value || null
            };

            if (jobData.frequency_type === 'every') {
                jobData.frequency_every_min = parseInt(document.getElementById('frequencyEveryMin').value);
            } else {
                jobData.day_mon = document.getElementById('dayMon').checked;
                jobData.day_tue = document.getElementById('dayTue').checked;
                jobData.day_wed = document.getElementById('dayWed').checked;
                jobData.day_thu = document.getElementById('dayThu').checked;
                jobData.day_fri = document.getElementById('dayFri').checked;
                jobData.day_sat = document.getElementById('daySat').checked;
                jobData.day_sun = document.getElementById('daySun').checked;
                jobData.frequency_at_hr = parseInt(document.getElementById('frequencyAtHr').value);
                jobData.frequency_at_min = parseInt(document.getElementById('frequencyAtMin').value);
            }

            try {
                let response;
                if (isEditMode) {
                    // Update existing job
                    response = await fetch('/proxy/update', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            instance_url: currentInstance,
                            job_id: currentJobId,
                            job_data: jobData
                        })
                    });
                } else {
                    // Create new job
                    response = await fetch('/proxy/create', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            instance_url: currentInstance,
                            job_data: jobData
                        })
                    });
                }

                if (!response.ok) {
                    const error = await response.json();
                    alert('Failed to save job: ' + (error.error || 'Unknown error'));
                    return;
                }

                // Close modal and reload page
                closeJobModal();
                location.reload();
            } catch (error) {
                alert('Failed to save job: ' + error.message);
            }
        }
    </script>
</body>
</html>

import os
import requests
import json
from bottle import Bottle, template, static_file, request, response, TEMPLATE_PATH

app = Bottle()

# Template directory
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
TEMPLATE_PATH.insert(0, TEMPLATE_DIR)


def get_instances():
    """Parse instance configurations from environment variables

    Expected format:
    CRONISHE_INSTANCES=name1:url1,name2:url2

    Example:
    CRONISHE_INSTANCES=Production:http://localhost:48080,Staging:http://localhost:48081
    """
    instances_env = os.getenv('CRONISHE_INSTANCES', '')
    instances = []

    if instances_env:
        for instance_str in instances_env.split(','):
            parts = instance_str.strip().split(':', 1)
            if len(parts) == 2:
                name, url = parts
                instances.append({
                    'name': name.strip(),
                    'url': url.strip().rstrip('/')
                })

    # Fallback to default local instance if no instances configured
    if not instances:
        instances.append({
            'name': 'Local',
            'url': 'http://localhost:48080'
        })

    return instances


def fetch_jobs(instance_url, timeout=5):
    """Fetch jobs from a Cronishe instance"""
    try:
        response = requests.get(f"{instance_url}/api/jobs", timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching jobs from {instance_url}: {e}")
        return None


@app.route('/')
def index():
    """Main page - list all instances and their jobs"""
    instances = get_instances()

    # Fetch jobs for each instance
    instances_data = []
    for instance in instances:
        jobs = fetch_jobs(instance['url'])
        instances_data.append({
            'name': instance['name'],
            'url': instance['url'],
            'jobs': jobs if jobs is not None else [],
            'error': jobs is None
        })

    return template('manager_index', instances=instances_data)


@app.route('/proxy/toggle', method='POST')
def proxy_toggle():
    """Proxy toggle job request to target instance"""
    response.content_type = 'application/json'

    try:
        data = request.json
        if not data or 'instance_url' not in data or 'job_id' not in data:
            response.status = 400
            return json.dumps({'error': 'Missing instance_url or job_id'})

        instance_url = data['instance_url']
        job_id = data['job_id']

        # Forward toggle request to instance
        resp = requests.post(f"{instance_url}/api/job/{job_id}/toggle", timeout=10)
        resp.raise_for_status()

        return resp.text

    except requests.RequestException as e:
        response.status = 500
        return json.dumps({'error': f'Failed to toggle job: {str(e)}'})
    except Exception as e:
        response.status = 500
        return json.dumps({'error': str(e)})


@app.route('/proxy/delete', method='POST')
def proxy_delete():
    """Proxy delete job request to target instance"""
    response.content_type = 'application/json'

    try:
        data = request.json
        if not data or 'instance_url' not in data or 'job_id' not in data:
            response.status = 400
            return json.dumps({'error': 'Missing instance_url or job_id'})

        instance_url = data['instance_url']
        job_id = data['job_id']

        # Forward delete request to instance
        resp = requests.delete(f"{instance_url}/api/job/{job_id}", timeout=10)
        resp.raise_for_status()

        return resp.text

    except requests.RequestException as e:
        response.status = 500
        return json.dumps({'error': f'Failed to delete job: {str(e)}'})
    except Exception as e:
        response.status = 500
        return json.dumps({'error': str(e)})


@app.route('/proxy/create', method='POST')
def proxy_create():
    """Proxy create job request to target instance"""
    response.content_type = 'application/json'

    try:
        data = request.json
        if not data or 'instance_url' not in data or 'job_data' not in data:
            response.status = 400
            return json.dumps({'error': 'Missing instance_url or job_data'})

        instance_url = data['instance_url']
        job_data = data['job_data']

        # Forward create request to instance
        resp = requests.post(f"{instance_url}/api/job", json=job_data, timeout=10)
        resp.raise_for_status()

        return resp.text

    except requests.RequestException as e:
        response.status = 500
        return json.dumps({'error': f'Failed to create job: {str(e)}'})
    except Exception as e:
        response.status = 500
        return json.dumps({'error': str(e)})


@app.route('/proxy/update', method='POST')
def proxy_update():
    """Proxy update job request to target instance"""
    response.content_type = 'application/json'

    try:
        data = request.json
        if not data or 'instance_url' not in data or 'job_id' not in data or 'job_data' not in data:
            response.status = 400
            return json.dumps({'error': 'Missing instance_url, job_id, or job_data'})

        instance_url = data['instance_url']
        job_id = data['job_id']
        job_data = data['job_data']

        # Forward update request to instance
        resp = requests.put(f"{instance_url}/api/job/{job_id}", json=job_data, timeout=10)
        resp.raise_for_status()

        return resp.text

    except requests.RequestException as e:
        response.status = 500
        return json.dumps({'error': f'Failed to update job: {str(e)}'})
    except Exception as e:
        response.status = 500
        return json.dumps({'error': str(e)})


@app.route('/proxy/runs', method='POST')
def proxy_runs():
    """Proxy job runs request to target instance"""
    response.content_type = 'application/json'

    try:
        data = request.json
        if not data or 'instance_url' not in data or 'job_id' not in data:
            response.status = 400
            return json.dumps({'error': 'Missing instance_url or job_id'})

        instance_url = data['instance_url']
        job_id = data['job_id']

        # Forward runs request to instance
        resp = requests.get(f"{instance_url}/api/job/{job_id}/runs", timeout=10)
        resp.raise_for_status()

        return resp.text

    except requests.RequestException as e:
        response.status = 500
        return json.dumps({'error': f'Failed to fetch runs: {str(e)}'})
    except Exception as e:
        response.status = 500
        return json.dumps({'error': str(e)})


@app.route('/proxy/logs', method='POST')
def proxy_logs():
    """Proxy run logs request to target instance"""
    response.content_type = 'application/json'

    try:
        data = request.json
        if not data or 'instance_url' not in data or 'run_id' not in data:
            response.status = 400
            return json.dumps({'error': 'Missing instance_url or run_id'})

        instance_url = data['instance_url']
        run_id = data['run_id']

        # Forward logs request to instance
        resp = requests.get(f"{instance_url}/api/run/{run_id}/logs", timeout=10)
        resp.raise_for_status()

        return resp.text

    except requests.RequestException as e:
        response.status = 500
        return json.dumps({'error': f'Failed to fetch logs: {str(e)}'})
    except Exception as e:
        response.status = 500
        return json.dumps({'error': str(e)})


@app.route('/proxy/run', method='POST')
def proxy_run_now():
    """Proxy run now request to target instance"""
    response.content_type = 'application/json'

    try:
        data = request.json
        if not data or 'instance_url' not in data or 'job_id' not in data:
            response.status = 400
            return json.dumps({'error': 'Missing instance_url or job_id'})

        instance_url = data['instance_url']
        job_id = data['job_id']

        # Forward run request to instance
        resp = requests.post(f"{instance_url}/api/job/{job_id}/run", timeout=10)
        resp.raise_for_status()

        return resp.text

    except requests.RequestException as e:
        response.status = 500
        return json.dumps({'error': f'Failed to run job: {str(e)}'})
    except Exception as e:
        response.status = 500
        return json.dumps({'error': str(e)})


@app.route('/static/<filename>')
def server_static(filename):
    """Serve static files"""
    return static_file(filename, root=os.path.join(os.path.dirname(__file__), 'static'))


if __name__ == '__main__':
    # Run web server
    port = int(os.getenv('MANAGER_PORT', 48090))
    app.run(host='0.0.0.0', port=port, debug=True)

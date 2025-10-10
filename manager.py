import os
import requests
from bottle import Bottle, template, static_file, TEMPLATE_PATH

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


@app.route('/static/<filename>')
def server_static(filename):
    """Serve static files"""
    return static_file(filename, root=os.path.join(os.path.dirname(__file__), 'static'))


if __name__ == '__main__':
    # Run web server
    port = int(os.getenv('MANAGER_PORT', 48090))
    app.run(host='0.0.0.0', port=port, debug=True)

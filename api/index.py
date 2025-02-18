import sys
import os
import importlib.util

# Get the absolute path of the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Dynamically import the create_app function
def import_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import create_app from app.py
app_module = import_from_path('app', os.path.join(project_root, 'app.py'))
create_app = app_module.create_app

# Import request from flask
flask_module = import_from_path('flask', os.path.join(project_root, 'flask.py'))
request = flask_module.request

# Create the Flask app
app = create_app()

# Vercel serverless function handler
def handler(event, context):
    # Convert Vercel event to Flask request
    flask_request = {
        'method': event.get('method', 'GET'),
        'path': event.get('path', '/'),
        'headers': event.get('headers', {}),
        'query': event.get('query', {}),
        'body': event.get('body', '')
    }

    # Simulate Flask request context
    with app.request_context(flask_request):
        # Handle the request
        response = app.full_dispatch_request()
        
        # Convert Flask response to Vercel response format
        return {
            'statusCode': response.status_code,
            'headers': dict(response.headers),
            'body': response.get_data(as_text=True)
        }

# WSGI application for local development
application = app

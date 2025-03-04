import sys
import os
import json
from urllib.parse import parse_qs

# Get the absolute path of the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import create_app

# Create the Flask app
app = create_app()

def handler(request, context):
    """
    Vercel serverless function handler
    """
    # Get request details
    http_method = request.get('method', 'GET')
    path = request.get('path', '/')
    headers = request.get('headers', {})
    body = request.get('body', '')
    query_params = request.get('query', {})

    # Convert query params to Flask format
    if query_params:
        path += '?' + '&'.join(f"{k}={v}" for k, v in query_params.items())

    # Create test environment
    environ = {
        'REQUEST_METHOD': http_method,
        'PATH_INFO': path,
        'CONTENT_TYPE': headers.get('content-type', ''),
        'CONTENT_LENGTH': str(len(body)) if body else '0',
        'HTTP_HOST': headers.get('host', 'localhost'),
    }

    # Add headers
    for key, value in headers.items():
        key = 'HTTP_' + key.upper().replace('-', '_')
        environ[key] = value

    # Create test client
    with app.test_client() as client:
        # Make the request
        response = client.open(
            path=path,
            method=http_method,
            data=body,
            environ_base=environ
        )

        # Get response data
        response_data = response.get_data()
        if isinstance(response_data, bytes):
            response_data = response_data.decode('utf-8')

        # Return Vercel response format
        return {
            'statusCode': response.status_code,
            'headers': dict(response.headers),
            'body': response_data
        }

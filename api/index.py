from http.server import BaseHTTPRequestHandler
from flask import Flask, Response
import sys
import os

# Get the absolute path of the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import create_app

# Create the Flask app
app = create_app()

def handler(request):
    """
    Vercel serverless function handler
    """
    # Get the path from the request
    path = request.get('path', '/')
    if path.endswith('/'):
        path = path[:-1]
    
    # Get the HTTP method
    method = request.get('method', 'GET')
    
    # Create the environment for Flask
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': '',
        'SERVER_NAME': 'vercel',
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': None,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }

    # Add query parameters if present
    if 'query' in request:
        environ['QUERY_STRING'] = '&'.join(f"{k}={v}" for k, v in request['query'].items())

    # Add headers
    if 'headers' in request:
        for key, value in request['headers'].items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                key = f'HTTP_{key}'
            environ[key] = value

    # Handle the request body
    if 'body' in request and request['body']:
        environ['wsgi.input'] = request['body']
        environ['CONTENT_LENGTH'] = str(len(request['body']))

    # Create response headers list
    headers_set = []
    headers_sent = []

    def write(data):
        """Write response data"""
        headers_sent[:] = headers_set[:]
        return data

    def start_response(status, response_headers, exc_info=None):
        """Start the response"""
        headers_set[:] = [status, response_headers]
        return write

    # Get response from Flask app
    response = app(environ, start_response)
    
    # Get status code
    status_code = int(headers_set[0].split()[0])
    
    # Convert headers to dict
    headers = dict(headers_set[1])
    
    # Get response body
    body = b''.join(response)
    
    # Return response in Vercel format
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': body.decode('utf-8')
    }

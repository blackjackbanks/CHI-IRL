import sys
import os
import json

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from flask import request

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

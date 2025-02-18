import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# Vercel requires the app to be named 'app'
app = create_app()

# This is required for Vercel serverless functions
def handler(event, context):
    return app(event, context)

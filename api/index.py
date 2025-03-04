from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

# Import project-specific modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from event_scraper import EventScraper
from google_calendar_sync import get_calendar_service

app = Flask(__name__)
CORS(app)  # Enable CORS for Carrd integration

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Event Scraper API",
        "endpoints": {
            "add_event": "/add_event",
            "supported_sources": ["Meetup.com", "mHUB Chicago"]
        }
    })

@app.route('/add_event', methods=['POST'])
def add_event():
    # Handle both JSON and form data
    if request.is_json:
        event_url = request.json.get('event_url')
    else:
        event_url = request.form.get('event_url')
    
    if not event_url:
        return jsonify({"error": "No event URL provided"}), 400
    
    try:
        print(f"\nProcessing event URL: {event_url}")
        scraper = EventScraper()
        service = get_calendar_service()
        
        print("Successfully got calendar service")
        result = scraper.process_and_add_event(event_url, service)
        
        if result:
            return jsonify({
                "status": "success",
                "event_details": result
            }), 200
        else:
            print("Failed to process event - no result returned")
            return jsonify({
                "error": "Could not process event",
                "url": event_url
            }), 422
    
    except Exception as e:
        print(f"Error processing event: {e}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

def handler(request):
    """Handle incoming request"""
    with app.test_request_context(
        path=request.get('path', '/'),
        method=request.get('method', 'GET'),
        headers=request.get('headers', {}),
        data=request.get('body', '')
    ):
        try:
            response = app.full_dispatch_request()
            return {
                'statusCode': response.status_code,
                'headers': dict(response.headers),
                'body': response.get_data(as_text=True)
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': str(e)
            }

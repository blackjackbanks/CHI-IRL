import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import project-specific modules
from event_scraper import EventScraper
from google_calendar_sync import get_calendar_service

def create_app():
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

    return app

# For local development
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

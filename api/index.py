from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
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
    
    return jsonify({"message": "Event processing temporarily disabled"}), 200

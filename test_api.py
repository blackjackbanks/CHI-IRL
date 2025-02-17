import requests
import json

def test_add_event():
    # Test endpoint
    url = 'http://localhost:5000/add_event'
    
    # Test data - replace with a real event URL
    test_event = {
        'event_url': 'https://www.meetup.com/bootstrappers-breakfast-chicago/events/304560800/'  # Replace with a real event URL
    }
    
    # Make request
    response = requests.post(url, json=test_event)
    
    # Print results
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))

if __name__ == '__main__':
    test_add_event()

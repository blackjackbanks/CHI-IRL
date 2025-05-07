import os
import logging
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('calendar_api_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_calendar_service():
    """Get Google Calendar service using OAuth flow"""
    creds = None
    
    # The token.pickle file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logging.error("No valid credentials found. Please run process_events.py first to authenticate.")
            return None
    
    return build('calendar', 'v3', credentials=creds)

def test_regular_event():
    """Test creating a regular timed event"""
    service = get_calendar_service()
    if not service:
        return
    
    # Create a test event for tomorrow
    now = datetime.now()
    start_time = datetime(now.year, now.month, now.day, 10, 0) + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)
    
    event = {
        'summary': 'Test Regular Event',
        'location': 'Test Location',
        'description': 'This is a test event to verify the Google Calendar API integration',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'America/Chicago',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'America/Chicago',
        },
    }
    
    try:
        logging.info("Creating regular test event...")
        logging.info(f"Start time: {event['start']['dateTime']}")
        logging.info(f"End time: {event['end']['dateTime']}")
        
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        logging.info(f"Success! Event created: {created_event.get('htmlLink')}")
        return created_event['id']
    except Exception as e:
        logging.error(f"Error creating regular event: {str(e)}")
        logging.error(f"Event data that caused error: {event}")
        return None

def test_all_day_event():
    """Test creating an all-day event"""
    service = get_calendar_service()
    if not service:
        return
    
    # Create a test all-day event for tomorrow
    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day) + timedelta(days=1)
    end_date = start_date + timedelta(days=1)  # End date is exclusive in Google Calendar
    
    event = {
        'summary': 'Test All-Day Event',
        'location': 'Test Location',
        'description': 'This is a test all-day event to verify the Google Calendar API integration',
        'start': {
            'date': start_date.date().isoformat(),
            'timeZone': 'America/Chicago',
        },
        'end': {
            'date': end_date.date().isoformat(),
            'timeZone': 'America/Chicago',
        },
    }
    
    try:
        logging.info("Creating all-day test event...")
        logging.info(f"Start date: {event['start']['date']}")
        logging.info(f"End date: {event['end']['date']}")
        
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        logging.info(f"Success! All-day event created: {created_event.get('htmlLink')}")
        return created_event['id']
    except Exception as e:
        logging.error(f"Error creating all-day event: {str(e)}")
        logging.error(f"Event data that caused error: {event}")
        return None

def delete_test_events(event_ids):
    """Delete test events"""
    service = get_calendar_service()
    if not service:
        return
    
    for event_id in event_ids:
        try:
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            logging.info(f"Deleted test event: {event_id}")
        except Exception as e:
            logging.error(f"Error deleting test event {event_id}: {str(e)}")

def main():
    logging.info("Starting Google Calendar API test...")
    
    # Test regular event
    regular_event_id = test_regular_event()
    
    # Test all-day event
    all_day_event_id = test_all_day_event()
    
    # Clean up test events
    event_ids = [eid for eid in [regular_event_id, all_day_event_id] if eid]
    if event_ids:
        input("Press Enter to delete the test events...")
        delete_test_events(event_ids)
    
    logging.info("Google Calendar API test completed.")

if __name__ == "__main__":
    main()

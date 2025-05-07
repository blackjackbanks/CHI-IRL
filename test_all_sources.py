import os
import logging
import pickle
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from event_scraper import EventScraper
from google_drive_helper import GoogleDriveHelper
from dateutil import parser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('all_sources_test.log', encoding='utf-8'),
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

def create_calendar_event(event_details):
    """Create a Google Calendar event from scraped event details"""
    start_datetime = event_details.get('start_datetime')
    end_datetime = event_details.get('end_datetime')
    
    # Format the start and end times for the calendar API
    if isinstance(start_datetime, str):
        # Try to parse the string to a datetime object
        start_datetime = parser.parse(start_datetime)
    
    if isinstance(end_datetime, str):
        # Try to parse the string to a datetime object
        end_datetime = parser.parse(end_datetime)
    
    # If end_datetime is not provided, set it to 2 hours after start
    if not end_datetime and start_datetime:
        end_datetime = start_datetime + timedelta(hours=2)
    
    # Check if it's an all-day event
    is_all_day = False
    if start_datetime and not start_datetime.hour and not start_datetime.minute and not start_datetime.second:
        # Check if it's exactly at midnight, which suggests an all-day event
        is_all_day = True
    
    # Create the event dictionary
    calendar_event = {
        'summary': event_details.get('title', 'Untitled Event'),
        'location': event_details.get('location', ''),
        'description': event_details.get('description', ''),
    }
    
    # Set the start and end times
    if is_all_day:
        # Format for all-day event
        calendar_event['start'] = {
            'date': start_datetime.strftime('%Y-%m-%d')
        }
        calendar_event['end'] = {
            'date': end_datetime.strftime('%Y-%m-%d')
        }
    else:
        # Format for regular event with time
        calendar_event['start'] = {
            'dateTime': start_datetime.isoformat()
        }
        calendar_event['end'] = {
            'dateTime': end_datetime.isoformat()
        }
    
    return calendar_event

def test_event_source(url, source_name):
    """Test scraping and adding an event from a specific source"""
    logging.info(f"Testing {source_name} event: {url}")
    
    # Initialize scraper
    scraper = EventScraper()
    
    # Get event details
    event_details = scraper.get_event_details(url)
    
    if not event_details:
        logging.error(f"Failed to scrape {source_name} event details from {url}")
        return False
    
    logging.info(f"Successfully scraped {source_name} event: {event_details.get('title')}")
    logging.info(f"Start time: {event_details.get('start_datetime')}")
    logging.info(f"End time: {event_details.get('end_datetime')}")
    
    # Get calendar service
    calendar_service = get_calendar_service()
    if not calendar_service:
        logging.error("Failed to get calendar service")
        return False
    
    # Add event to calendar
    try:
        # Create calendar event
        calendar_event = create_calendar_event(event_details)
        
        # Add test prefix to title
        calendar_event['summary'] = f"[TEST] {calendar_event['summary']}"
        
        # Add a single RSVP link to the description
        rsvp_link = f'<a href="{url}">RSVP</a><br><br>'
        description = calendar_event.get('description', '')
        calendar_event['description'] = rsvp_link + description
        
        # Handle image attachment if available
        image_url = event_details.get('image_url')
        if image_url:
            # Initialize Drive helper
            drive_helper = GoogleDriveHelper(None)  # Using default credentials
            
            # Upload image to Drive
            image_id, drive_link = drive_helper.upload_image_from_url(
                image_url, 
                calendar_event['summary']
            )
            
            if image_id and drive_link:
                # Get file details
                file_details = drive_helper.service.files().get(fileId=image_id).execute()
                
                # Add attachment to event
                calendar_event['attachments'] = [{
                    'fileUrl': drive_link,
                    'mimeType': file_details.get('mimeType', 'image/jpeg'),
                    'title': file_details.get('name', 'Event Image')
                }]
        
        logging.info(f"Attempting to add event to calendar: {calendar_event['summary']}")
        
        # Check if it's an all-day event
        if 'date' in calendar_event['start']:
            logging.info(f"All-day event detected")
            logging.info(f"Start date: {calendar_event['start']['date']}")
            logging.info(f"End date: {calendar_event['end']['date']}")
        else:
            logging.info(f"Start time: {calendar_event['start']['dateTime']}")
            logging.info(f"End time: {calendar_event['end']['dateTime']}")
        
        # Add supportsAttachments parameter if we have attachments
        extra_params = {}
        if 'attachments' in calendar_event:
            extra_params['supportsAttachments'] = True
        
        created_event = calendar_service.events().insert(
            calendarId='primary',
            body=calendar_event,
            **extra_params
        ).execute()
        
        logging.info(f"Success! Event created: {created_event.get('htmlLink')}")
        return created_event['id']
    except Exception as e:
        logging.error(f"Error adding {source_name} event to calendar: {str(e)}")
        logging.error(f"Event data that caused error: {calendar_event}")
        return False

def delete_test_events(event_ids):
    """Delete test events"""
    calendar_service = get_calendar_service()
    if not calendar_service:
        return
    
    for event_id in event_ids:
        try:
            calendar_service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            logging.info(f"Deleted test event: {event_id}")
        except Exception as e:
            logging.error(f"Error deleting test event {event_id}: {str(e)}")

def main():
    logging.info("Starting comprehensive event source test...")
    
    # Test URLs for each source
    test_urls = {
        "Meetup": "https://www.meetup.com/chicago-react-native-meetup/events/306127251/",
        "Lu.ma": "https://lu.ma/9x1ss8b2",
        "1871": "https://community.1871.com/events/innovation-summit-emerging-tech",
        "mHUB": "https://mhubchicago.com/event/march-happy-hour-130849"
    }
    
    event_ids = []
    
    # Test each source
    for source, url in test_urls.items():
        event_id = test_event_source(url, source)
        if event_id:
            event_ids.append(event_id)
    
    # Clean up test events
    if event_ids:
        input("Press Enter to delete the test events...")
        delete_test_events(event_ids)
    
    logging.info("Comprehensive event source test completed.")

if __name__ == "__main__":
    main()

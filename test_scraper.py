import sys
import os
import json
import logging
from datetime import datetime, timedelta

# Configure logging to handle Unicode
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('calendar_sync.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google_calendar_sync import GoogleCalendarSync, EventScraper

def sanitize_for_logging(text):
    """
    Sanitize text to remove problematic Unicode characters for logging
    """
    return ''.join(char for char in text if char.isprintable())

def test_event_scraping(url):
    """
    Test event scraping for a specific URL
    """
    scraper = EventScraper()
    
    logging.info(f"Testing URL: {url}")
    try:
        event_details = scraper.get_event_details(url)
        
        if event_details:
            logging.info("Successful scrape!")
            
            # Sanitize description for logging
            safe_description = sanitize_for_logging(event_details.get('description', 'No Description'))
            logging.debug(f"Scraped Event Details: {json.dumps(event_details, indent=2, default=str)}")
            
            # Optional: Test Google Calendar integration
            try:
                logging.info("Attempting to get Google Calendar service...")
                calendar_service = GoogleCalendarSync().get_calendar_service()
                logging.info("Successfully obtained calendar service")
                
                # Detailed logging of event details before adding
                logging.debug("Event Details for Calendar:")
                logging.debug(f"Title: {event_details.get('title', 'No Title')}")
                logging.debug(f"Start: {event_details.get('start_datetime', 'No Start Time')}")
                logging.debug(f"End: {event_details.get('end_datetime', 'No End Time')}")
                logging.debug(f"Location: {event_details.get('location', 'No Location')}")
                logging.debug(f"Description: {safe_description}")
                
                # Add event to calendar
                event = {
                    'summary': event_details.get('title', 'No Title'),
                    'location': event_details.get('location', ''),
                    'description': event_details.get('description', ''),
                    'start': {
                        'dateTime': event_details['start_datetime'].isoformat(),
                        'timeZone': 'America/Chicago',
                    },
                    'end': {
                        'dateTime': event_details['end_datetime'].isoformat(),
                        'timeZone': 'America/Chicago',
                    },
                }
                
                logging.info("Attempting to insert event into calendar...")
                created_event = calendar_service.events().insert(
                    calendarId='primary',
                    body=event
                ).execute()
                
                logging.info(f"Successfully created calendar event: {created_event['id']}")
                logging.info(f"Event link: {created_event.get('htmlLink', 'No link available')}")
                
                return event_details
            except Exception as e:
                logging.error(f"Could not add event to Google Calendar: {str(e)}")
                logging.exception("Full traceback:")
                return None
        else:
            logging.warning(f"Failed to scrape event from {url}")
            return None
    
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        logging.exception("Full traceback:")
        return None

def main():
    # Test URLs for different event sources
    test_urls = [
        # Meetup event
        'https://www.meetup.com/bootstrappers-breakfast-chicago/events/304560800/',
        
        # mHUB event
        'https://www.mhubchicago.com/events/startup-showcase',
        
        # Lu.Ma event
        'https://lu.ma/k2yrxjr1'
    ]
    
    # Allow manual URL input
    if len(sys.argv) > 1:
        test_urls = [sys.argv[1]]
    
    for url in test_urls:
        test_event_scraping(url)
        
        # Explicitly print to console
        print("\n--- Detailed Scraper Output ---")
        with open('calendar_sync.log', 'r', encoding='utf-8') as log_file:
            print(log_file.read())

if __name__ == '__main__':
    main()

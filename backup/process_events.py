import csv
import logging
import os
import pickle
import requests
import re
import time
import random
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
from event_scraper import EventScraper
from google_drive_helper import GoogleDriveHelper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('calendar_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/drive']

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
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds), creds

def select_calendar(service):
    """Allow user to select a calendar"""
    # List all available calendars
    calendars_result = service.calendarList().list().execute()
    calendars = calendars_result.get('items', [])
    
    if not calendars:
        logging.info("No calendars found.")
        return 'primary'
    
    # Display calendars
    logging.info("Available calendars:")
    for i, calendar in enumerate(calendars):
        logging.info(f"{i+1}. {calendar['summary']} ({calendar['id']})")
    
    # Ask for selection
    try:
        selection = input("\nSelect calendar number (or press Enter for primary calendar): ")
        if selection.strip():
            index = int(selection) - 1
            if 0 <= index < len(calendars):
                calendar_id = calendars[index]['id']
                logging.info(f"Selected calendar: {calendars[index]['summary']}")
                return calendar_id
    except:
        pass
    
    logging.info("Using primary calendar")
    return 'primary'

def get_meetup_event_title(url):
    """Get a better title for Meetup events by scraping the page"""
    try:
        logging.info(f"Fetching better title for Meetup event: {url}")
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find the event title in different elements
        title_element = soup.find('h1', {'data-testid': 'event-title'})
        if not title_element:
            title_element = soup.find('h1', {'class': 'text-display2'})
        if not title_element:
            title_element = soup.find('meta', {'property': 'og:title'})
            if title_element:
                return title_element.get('content')
        
        if title_element:
            title = title_element.text.strip()
            logging.info(f"Found Meetup event title: {title}")
            return title
        
        # If we can't find the title, extract group name from URL
        parts = url.split('/')
        if len(parts) >= 5:
            group_name = parts[3].replace('-', ' ').title()
            return f"Meetup: {group_name}"
            
    except Exception as e:
        logging.error(f"Error getting Meetup event title: {e}")
    
    return None

def get_eventbrite_event_title(url):
    """Get a better title for Eventbrite events by scraping the page"""
    try:
        logging.info(f"Fetching better title for Eventbrite event: {url}")
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find the event title in structured data first (most reliable)
        script_tags = soup.find_all('script', {'type': 'application/ld+json'})
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('name'):
                    title = data.get('name')
                    logging.info(f"Found Eventbrite event title from JSON-LD: {title}")
                    return title
            except:
                pass
        
        # Try to find the event title in different elements
        title_element = soup.find('h1', {'class': 'event-title'})
        if not title_element:
            title_element = soup.find('h1', {'data-automation': 'listing-title'})
        if not title_element:
            title_element = soup.find('meta', {'property': 'og:title'})
            if title_element:
                return title_element.get('content')
        
        if title_element:
            title = title_element.text.strip()
            logging.info(f"Found Eventbrite event title: {title}")
            return title
        
        # If we can't find the title, extract event name from URL
        parts = url.split('/')
        if len(parts) >= 5:
            event_name = parts[4].split('-tickets-')[0].replace('-', ' ').title()
            return f"Eventbrite: {event_name}"
            
    except Exception as e:
        logging.error(f"Error getting Eventbrite event title: {e}")
    
    return None

def get_eventbrite_image_url(url):
    """Get a better image URL for Eventbrite events by scraping the page"""
    try:
        logging.info(f"Fetching better image URL for Eventbrite event: {url}")
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find the image URL in structured data first (most reliable)
        script_tags = soup.find_all('script', {'type': 'application/ld+json'})
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('image'):
                    image_url = data.get('image')
                    if isinstance(image_url, list) and len(image_url) > 0:
                        image_url = image_url[0]
                    logging.info(f"Found Eventbrite image URL from JSON-LD: {image_url}")
                    return image_url
            except:
                pass
        
        # Try to find the image in meta tags
        og_image = soup.find('meta', {'property': 'og:image'})
        if og_image and og_image.get('content'):
            return og_image.get('content')
        
        # Try to find image in other common elements
        img_element = soup.find('img', {'class': 'event-header__image'})
        if img_element and img_element.get('src'):
            return img_element.get('src')
            
    except Exception as e:
        logging.error(f"Error getting Eventbrite image URL: {e}")
    
    return None

def validate_event_data(event_details):
    """
    Validate event data before sending to Google Calendar API.
    Returns a tuple (is_valid, validation_errors)
    """
    validation_errors = []
    
    # Check required fields
    if not event_details.get('title'):
        validation_errors.append("Missing event title")
    elif len(event_details['title']) > 1024:
        validation_errors.append(f"Event title too long: {len(event_details['title'])} chars (max 1024)")
    
    # Validate start and end times
    if not event_details.get('start_datetime'):
        validation_errors.append("Missing start datetime")
    
    if not event_details.get('end_datetime'):
        validation_errors.append("Missing end datetime")
    
    # Ensure start time is before end time
    if event_details.get('start_datetime') and event_details.get('end_datetime'):
        if event_details['start_datetime'] > event_details['end_datetime']:
            validation_errors.append(f"Start time ({event_details['start_datetime']}) is after end time ({event_details['end_datetime']})")
    
    # Validate location (optional but if present should be valid)
    if event_details.get('location') and len(event_details['location']) > 1024:
        validation_errors.append(f"Location too long: {len(event_details['location'])} chars (max 1024)")
    
    # No length constraint for description - allow full descriptions
    
    # Check for invalid characters in text fields
    for field in ['title', 'location', 'description']:
        if event_details.get(field):
            # Check for control characters that might cause API issues
            if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', event_details[field]):
                validation_errors.append(f"Invalid control characters found in {field}")
                # Clean the field
                event_details[field] = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', event_details[field])
    
    return (len(validation_errors) == 0, validation_errors, event_details)

def retry_with_backoff(func, max_retries=5, initial_delay=1, max_delay=60):
    """
    Retry a function with exponential backoff
    
    Args:
        func: The function to retry
        max_retries: Maximum number of retries before giving up
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
    
    Returns:
        The result of the function call, or raises the last exception if all retries fail
    """
    retries = 0
    delay = initial_delay
    
    while retries < max_retries:
        try:
            return func()
        except Exception as e:
            retries += 1
            if retries == max_retries:
                logging.error(f"Maximum retries ({max_retries}) reached. Giving up.")
                raise e
            
            # Calculate delay with jitter to avoid thundering herd problem
            jitter = random.uniform(0, 0.1 * delay)
            sleep_time = min(delay + jitter, max_delay)
            
            logging.warning(f"Retry {retries}/{max_retries} after error: {str(e)}. Waiting {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            
            # Exponential backoff
            delay = min(delay * 2, max_delay)

def process_events_from_csv(csv_path):
    """Process all events from CSV and add them to Google Calendar"""
    # Initialize scraper and services
    scraper = EventScraper()
    
    try:
        # Initialize Google Calendar
        logging.info("Initializing Google services...")
        calendar_service, creds = get_calendar_service()
        
        # Try to initialize Google Drive, but make it optional
        drive_helper = None
        try:
            drive_helper = GoogleDriveHelper('credentials.json')
            drive_helper.service = build('drive', 'v3', credentials=creds)
            
            # Test Drive permissions explicitly
            try:
                # Create folder for event images
                drive_helper.create_events_folder()
                logging.info(f"Using Google Drive folder ID: {drive_helper.folder_id}")
            except Exception as folder_error:
                if "insufficientPermissions" in str(folder_error) or "403" in str(folder_error):
                    logging.warning("Google Drive permissions are insufficient. Image attachments will be disabled.")
                    logging.warning("To fix this issue, delete token.pickle and re-authenticate with full Drive permissions.")
                    drive_helper = None
                else:
                    raise folder_error
        except Exception as e:
            logging.warning(f"Google Drive integration not available: {str(e)}")
            logging.warning("Will continue without Drive integration for images")
            drive_helper = None
        
        # Select calendar
        calendar_id = select_calendar(calendar_service)
        
        # Process events
        success_count = 0
        error_count = 0
        
        # Read CSV file
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f) if ',' in f.readline() else csv.reader(f)
            f.seek(0)  # Reset file pointer
            
            # If not a DictReader, skip header
            if not isinstance(reader, csv.DictReader):
                next(reader, None)
            
            # Process each event URL
            for row in reader:
                url = row['Event URL'] if isinstance(row, dict) and 'Event URL' in row else row[0]
                logging.info(f"Processing event URL: {url}")
                
                try:
                    # Get event details
                    event_details = scraper.get_event_details(url)
                    
                    if not event_details:
                        logging.error(f"Failed to scrape event details from {url}")
                        error_count += 1
                        continue
                    
                    # Validate event data
                    is_valid, validation_errors, event_details = validate_event_data(event_details)
                    if not is_valid:
                        logging.error(f"Validation errors for {url}: {validation_errors}")
                        error_count += 1
                        continue
                    
                    # Ensure we have a title
                    if not event_details.get('title') or event_details.get('title') == 'Unnamed Event':
                        # For Meetup events, try to get a better title
                        if 'meetup.com' in url:
                            better_title = get_meetup_event_title(url)
                            if better_title:
                                event_details['title'] = better_title
                                logging.info(f"Using better title: {better_title}")
                        # For Eventbrite events, try to get a better title
                        elif 'eventbrite.com' in url:
                            better_title = get_eventbrite_event_title(url)
                            if better_title:
                                event_details['title'] = better_title
                                logging.info(f"Using better title: {better_title}")
                    
                    # Add image attachment if available
                    image_url = event_details.get('image_url')
                    if image_url and drive_helper:
                        try:
                            # Log the image URL we're trying to use
                            logging.info(f"Attempting to upload image from URL: {image_url}")
                            
                            # For Eventbrite, ensure we have a valid image URL
                            if 'eventbrite.com' in url and not image_url.startswith(('http://', 'https://')):
                                # Try to extract a better image URL from the page
                                better_image_url = get_eventbrite_image_url(url)
                                if better_image_url:
                                    image_url = better_image_url
                                    logging.info(f"Using better image URL for Eventbrite: {image_url}")
                            
                            # Validate image URL format
                            if not image_url.startswith(('http://', 'https://')):
                                logging.warning(f"Invalid image URL format: {image_url}")
                                image_url = None
                            
                            # Check if image URL is accessible
                            if image_url:
                                try:
                                    # Use a HEAD request to check if the image exists without downloading it
                                    head_response = requests.head(image_url, timeout=10)
                                    if head_response.status_code != 200:
                                        logging.warning(f"Image URL returned status code {head_response.status_code}: {image_url}")
                                        image_url = None
                                    else:
                                        content_type = head_response.headers.get('content-type', '')
                                        if not content_type.startswith('image/'):
                                            logging.warning(f"URL does not point to an image (content-type: {content_type}): {image_url}")
                                            image_url = None
                                except Exception as img_check_error:
                                    logging.warning(f"Error checking image URL: {str(img_check_error)}")
                                    image_url = None
                            
                            if image_url:
                                # Use the upload_image_from_url method to upload to Drive
                                image_id, drive_link = drive_helper.upload_image_from_url(
                                    image_url, 
                                    event_details.get('title', 'Event')
                                )
                                
                                if image_id and drive_link:
                                    logging.info(f"Uploaded image to Drive: {drive_link}")
                                    
                                    # Get the file details from Drive
                                    file_details = drive_helper.service.files().get(fileId=image_id).execute()
                                    
                                    # Check if the description already has an RSVP link
                                    description = event_details.get('description', '')
                                    if not f'<a href="{url}">RSVP</a>' in description:
                                        rsvp_link = f'<a href="{url}">RSVP</a><br><br>'
                                        description = rsvp_link + description
                                    
                                    # Create event with attachment
                                    calendar_event = {
                                        'summary': event_details.get('title', 'Untitled Event'),
                                        'location': event_details.get('location', ''),
                                        'description': description,
                                        'attachments': [{
                                            'fileUrl': drive_link,
                                            'mimeType': file_details.get('mimeType', 'image/jpeg'),
                                            'title': file_details.get('name', 'Event Image')
                                        }]
                                    }
                                else:
                                    logging.warning(f"Failed to upload image to Drive: {image_url}")
                                    # Check if the description already has an RSVP link
                                    description = event_details.get('description', '')
                                    if not f'<a href="{url}">RSVP</a>' in description:
                                        rsvp_link = f'<a href="{url}">RSVP</a><br><br>'
                                        description = rsvp_link + description
                                    
                                    calendar_event = {
                                        'summary': event_details.get('title', 'Untitled Event'),
                                        'location': event_details.get('location', ''),
                                        'description': description,
                                    }
                            else:
                                logging.warning(f"Skipping invalid image URL")
                                # Check if the description already has an RSVP link
                                description = event_details.get('description', '')
                                if not f'<a href="{url}">RSVP</a>' in description:
                                    rsvp_link = f'<a href="{url}">RSVP</a><br><br>'
                                    description = rsvp_link + description
                                
                                calendar_event = {
                                    'summary': event_details.get('title', 'Untitled Event'),
                                    'location': event_details.get('location', ''),
                                    'description': description,
                                }
                        except Exception as e:
                            logging.error(f"Error processing image: {str(e)}")
                            # Check if the description already has an RSVP link
                            description = event_details.get('description', '')
                            if not f'<a href="{url}">RSVP</a>' in description:
                                rsvp_link = f'<a href="{url}">RSVP</a><br><br>'
                                description = rsvp_link + description
                            
                            calendar_event = {
                                'summary': event_details.get('title', 'Untitled Event'),
                                'location': event_details.get('location', ''),
                                'description': description,
                            }
                    else:
                        # Check if the description already has an RSVP link
                        description = event_details.get('description', '')
                        if not f'<a href="{url}">RSVP</a>' in description:
                            rsvp_link = f'<a href="{url}">RSVP</a><br><br>'
                            description = rsvp_link + description
                        
                        calendar_event = {
                            'summary': event_details.get('title', 'Untitled Event'),
                            'location': event_details.get('location', ''),
                            'description': description,
                        }
                    
                    # Create calendar event
                    try:
                        start_datetime = event_details['start_datetime']
                        end_datetime = event_details['end_datetime']
                        
                        if isinstance(start_datetime, str):
                            start_datetime = datetime.strptime(start_datetime, '%Y-%m-%d %H:%M:%S')
                        if isinstance(end_datetime, str):
                            end_datetime = datetime.strptime(end_datetime, '%Y-%m-%d %H:%M:%S')
                        
                        # Check if this is an all-day event (no time specified or starts at midnight and lasts 24 hours)
                        is_all_day = False
                        if (start_datetime.hour == 0 and start_datetime.minute == 0 and 
                            end_datetime.hour == 0 and end_datetime.minute == 0 and
                            (end_datetime - start_datetime).days >= 1):
                            is_all_day = True
                            logging.info(f"Detected all-day event: {event_details.get('title', 'Untitled Event')}")
                        
                        # Format differently for all-day events vs. timed events
                        if is_all_day:
                            # All-day events use 'date' instead of 'dateTime'
                            calendar_event['start'] = {
                                'date': start_datetime.date().isoformat(),
                                'timeZone': 'America/Chicago',
                            }
                            # For all-day events, the end date should be the day after the last day
                            # (Google Calendar's quirk)
                            calendar_event['end'] = {
                                'date': (end_datetime + timedelta(days=1)).date().isoformat(),
                                'timeZone': 'America/Chicago',
                            }
                        else:
                            # Regular timed events
                            calendar_event['start'] = {
                                'dateTime': start_datetime.isoformat(),
                                'timeZone': 'America/Chicago',
                            }
                            calendar_event['end'] = {
                                'dateTime': end_datetime.isoformat(),
                                'timeZone': 'America/Chicago',
                            }
                    except Exception as e:
                        logging.error(f"Error formatting datetime: {str(e)}")
                        error_count += 1
                        continue
                    
                    # Add the event to the calendar
                    try:
                        # Add supportsAttachments parameter if we have attachments
                        extra_params = {}
                        if 'attachments' in calendar_event:
                            extra_params['supportsAttachments'] = True
                        
                        # Use retry logic for the API call
                        def calendar_insert_with_retry():
                            return calendar_service.events().insert(
                                calendarId=calendar_id,
                                body=calendar_event,
                                **extra_params
                            ).execute()
                        
                        created_event = retry_with_backoff(calendar_insert_with_retry)
                        
                        logging.info(f"Successfully added event: {calendar_event['summary']}")
                        logging.info(f"Calendar link: {created_event.get('htmlLink')}")
                        success_count += 1
                    except Exception as e:
                        error_message = str(e)
                        logging.error(f"Google Calendar API Error: {error_message}")
                        
                        # Enhanced error logging for Invalid Value errors
                        if "Invalid Value" in error_message:
                            # Log each field to help identify the problematic one
                            logging.error("Detailed field inspection for Invalid Value error:")
                            
                            # Check summary/title
                            if 'summary' in calendar_event:
                                logging.error(f"summary: {len(calendar_event['summary'])} chars - '{calendar_event['summary'][:100]}...'")
                            
                            # Check location
                            if 'location' in calendar_event:
                                logging.error(f"location: {len(calendar_event['location'])} chars - '{calendar_event['location'][:100]}...'")
                            
                            # Check description
                            if 'description' in calendar_event:
                                logging.error(f"description: {len(calendar_event['description'])} chars - '{calendar_event['description'][:100]}...'")
                            
                            # Check start/end times
                            if 'start' in calendar_event:
                                logging.error(f"start: {calendar_event['start']}")
                            if 'end' in calendar_event:
                                logging.error(f"end: {calendar_event['end']}")
                            
                            # Check attachments
                            if 'attachments' in calendar_event:
                                for i, attachment in enumerate(calendar_event['attachments']):
                                    logging.error(f"attachment[{i}]: {attachment}")
                        
                        # Log the full event data that caused the error
                        logging.error(f"Event data that caused error: {calendar_event}")
                        error_count += 1
                    
                except Exception as e:
                    logging.error(f"Error processing {url}: {str(e)}")
                    error_count += 1
        
        # Print summary
        logging.info(f"\nProcessing complete!")
        logging.info(f"Successfully processed: {success_count} events")
        logging.info(f"Errors: {error_count} events")
        
    except Exception as e:
        logging.error(f"Error initializing Google services: {str(e)}")

if __name__ == '__main__':
    process_events_from_csv('events.csv')

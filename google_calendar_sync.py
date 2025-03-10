import os
import json
import csv
from datetime import datetime, timedelta
from dateutil import parser
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google_drive_helper import GoogleDriveHelper
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class EventScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_meetup_event(self, url):
        """Scrape event details from Meetup.com"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find event time
            time_element = soup.find('time')
            event_time = None
            if time_element and time_element.get('datetime'):
                event_time = parser.parse(time_element['datetime'])
            
            # Find event image
            image_url = None
            og_image = soup.find('meta', property='og:image')
            if og_image:
                image_url = og_image.get('content')
            
            return event_time, image_url
        except Exception as e:
            print(f"Error scraping Meetup event: {str(e)}")
            return None, None

    def scrape_mhub_event(self, url):
        """Scrape event details from mHUB website"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find event time (adjust selectors based on actual HTML structure)
            time_element = soup.find('div', class_='event-date') or soup.find('time')
            event_time = None
            if time_element:
                # Try to parse the date text
                try:
                    event_time = parser.parse(time_element.text, fuzzy=True)
                except:
                    pass
            
            # Find event image
            image_url = None
            og_image = soup.find('meta', property='og:image')
            if og_image:
                image_url = og_image.get('content')
            if not image_url:
                img_element = soup.find('img', class_='event-image')
                if img_element:
                    image_url = urljoin(url, img_element.get('src', ''))
            
            return event_time, image_url
        except Exception as e:
            print(f"Error scraping mHUB event: {str(e)}")
            return None, None

    def get_event_details(self, url):
        """Get event details based on URL"""
        if 'meetup.com' in url:
            return self.scrape_meetup_event(url)
        elif 'mhubchicago.com' in url:
            return self.scrape_mhub_event(url)
        else:
            print(f"Unsupported event URL format: {url}")
            return None, None

    def scrape_luma_event(self, url):
        """
        Scrape Lu.Ma event details
        
        Args:
            url (str): Lu.Ma event URL
        
        Returns:
            dict: Event details (start_datetime, end_datetime, image_url)
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find event time
            time_element = soup.find('div', class_='event-date') or soup.find('time')
            event_time = None
            if time_element:
                # Try to parse the date text
                try:
                    event_time = parser.parse(time_element.text, fuzzy=True)
                except:
                    pass
            
            # Find event image
            image_url = None
            og_image = soup.find('meta', property='og:image')
            if og_image:
                image_url = og_image.get('content')
            
            return {
                'start_datetime': event_time.isoformat() if event_time else None,
                'end_datetime': (event_time + timedelta(hours=2)).isoformat() if event_time else None,
                'image_url': image_url
            }
        except Exception as e:
            print(f"Error scraping Lu.Ma event: {str(e)}")
            return None

class GoogleCalendarSync:
    def __init__(self, credentials_path):
        self.credentials_path = credentials_path
        self.service = self._get_calendar_service()
        self.calendar_id = None
        self.scraped_data = {}
        self.drive_helper = GoogleDriveHelper(credentials_path)
        self.scraper = EventScraper()

    def load_scraped_data(self, json_path):
        """Load previously scraped event data"""
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    self.scraped_data = json.load(f)
                print(f"Loaded scraped data for {len(self.scraped_data)} events")
            else:
                print("No scraped data file found")
        except Exception as e:
            print(f"Error loading scraped data: {str(e)}")

    def _get_calendar_service(self):
        import os
        import base64
        import json
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        # Retrieve base64 encoded credentials from environment
        base64_credentials = os.environ.get('GOOGLE_CREDENTIALS_BASE64')
        
        if not base64_credentials:
            raise ValueError("No Google credentials found in environment. Set GOOGLE_CREDENTIALS_BASE64.")
        
        try:
            # Decode base64 credentials
            credentials_json = base64.b64decode(base64_credentials).decode('utf-8')
            credentials_dict = json.loads(credentials_json)
            
            # Create credentials object
            creds = Credentials.from_authorized_user_info(info=credentials_dict)
            
            # Build and return calendar service
            service = build('calendar', 'v3', credentials=creds)
            return service
        
        except Exception as e:
            print(f"Error loading Google Calendar credentials: {e}")
            raise

    def list_calendars(self):
        """List all available calendars and return a dictionary of names and IDs."""
        calendars_result = self.service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        
        if not calendars:
            print('No calendars found.')
            return {}
        
        print("\nAvailable Calendars:")
        calendar_dict = {}
        for i, calendar in enumerate(calendars, 1):
            print(f"{i}. {calendar['summary']} ({calendar.get('colorId', 'default')})")
            calendar_dict[i] = {'name': calendar['summary'], 'id': calendar['id']}
        
        return calendar_dict

    def select_calendar(self):
        """Prompt user to select a calendar and set it as the target."""
        calendars = self.list_calendars()
        if not calendars:
            print("Using primary calendar as fallback.")
            self.calendar_id = 'primary'
            return

        while True:
            try:
                choice = int(input("\nEnter the number of the calendar you want to use: "))
                if choice in calendars:
                    selected = calendars[choice]
                    self.calendar_id = selected['id']
                    print(f"\nSelected calendar: {selected['name']}")
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

    def add_events_from_csv(self, csv_path):
        """Add events from CSV file to the selected Google Calendar."""
        if not self.calendar_id:
            self.select_calendar()

        try:
            events_added = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    event_url = row.get('Event URL', '').strip()
                    if not event_url or event_url.lower() in ['', 'nan', 'none']:
                        continue
                        
                    try:
                        event_details = self.scraper.get_event_details(event_url)
                        if event_details:
                            # Add event to calendar
                            event = {
                                'summary': event_details[0],
                                'location': event_details[1],
                                'description': '',
                                'start': {
                                    'dateTime': event_details[0].isoformat(),
                                    'timeZone': 'America/Chicago',
                                },
                                'end': {
                                    'dateTime': (event_details[0] + timedelta(hours=2)).isoformat(),
                                    'timeZone': 'America/Chicago',
                                },
                            }
                            
                            created_event = self.service.events().insert(
                                calendarId=self.calendar_id,
                                body=event
                            ).execute()
                            
                            events_added.append(created_event['id'])
                            print(f"Added event: {event_details[0]}")
                            
                    except Exception as e:
                        print(f"Error adding event {event_url}: {str(e)}")
                        continue
                        
            print(f"Successfully added {len(events_added)} events to calendar")
            return events_added
            
        except Exception as e:
            print(f"Error reading CSV: {str(e)}")
            return []

    def add_luma_events(self, luma_urls):
        """
        Add Lu.Ma events to the selected Google Calendar
        
        Args:
            luma_urls (list): List of Lu.Ma event URLs to scrape and add
        
        Returns:
            list: List of added event IDs
        """
        if not self.calendar_id:
            print("No calendar selected. Please select a calendar first.")
            self.select_calendar()

        added_event_ids = []
        
        for url in luma_urls:
            try:
                print(f"\nProcessing Lu.Ma event: {url}")
                
                # Scrape Lu.Ma event details
                event_details = self.scraper.scrape_luma_event(url)
                
                if not event_details:
                    print(f"Could not scrape event details from {url}")
                    continue

                # Extract start and end times
                start_time = event_details.get('start_datetime')
                end_time = event_details.get('end_datetime')
                image_url = event_details.get('image_url')

                if not start_time:
                    print(f"No start time found for event: {url}")
                    continue

                # Prepare event for Google Calendar
                event = {
                    'summary': 'Lu.Ma Event',  # Default title, can be improved
                    'location': url,
                    'start': {
                        'dateTime': start_time,
                        'timeZone': 'America/Chicago',
                    },
                    'end': {
                        'dateTime': end_time or (datetime.fromisoformat(start_time) + timedelta(hours=2)).isoformat(),
                        'timeZone': 'America/Chicago',
                    },
                    'description': f'Event from Lu.Ma\nOriginal URL: {url}\n' + 
                                   (f'Event Image: {image_url}' if image_url else '')
                }

                # Add event to Google Calendar
                event_result = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
                added_event_ids.append(event_result['id'])
                
                print(f"Added event to calendar: {event_result['htmlLink']}")

                # Optionally upload event image to Google Drive
                if image_url:
                    try:
                        self.drive_helper.upload_image_from_url(image_url, 'Lu.Ma Event')
                    except Exception as img_error:
                        print(f"Could not upload event image: {str(img_error)}")

            except Exception as e:
                print(f"Error processing Lu.Ma event {url}: {str(e)}")

        return added_event_ids

def get_calendar_service():
    """
    Get Google Calendar service using base64 encoded credentials from environment
    
    Returns:
        googleapiclient.discovery.Resource: Authenticated Google Calendar service
    """
    import os
    import base64
    import json
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    # Retrieve base64 encoded credentials from environment
    base64_credentials = os.environ.get('GOOGLE_CREDENTIALS_BASE64')
    
    if not base64_credentials:
        raise ValueError("No Google credentials found in environment. Set GOOGLE_CREDENTIALS_BASE64.")
    
    try:
        # Decode base64 credentials
        credentials_json = base64.b64decode(base64_credentials).decode('utf-8')
        credentials_dict = json.loads(credentials_json)
        
        # Create credentials object
        creds = Credentials.from_authorized_user_info(info=credentials_dict)
        
        # Build and return calendar service
        service = build('calendar', 'v3', credentials=creds)
        return service
    
    except Exception as e:
        print(f"Error loading Google Calendar credentials: {e}")
        raise

def main():
    credentials_path = 'credentials.json'
    csv_path = 'Table2.csv'
    scraped_data_path = 'scraped_events.json'
    
    calendar_sync = GoogleCalendarSync(credentials_path)
    
    # Load scraped data if available
    calendar_sync.load_scraped_data(scraped_data_path)
    
    # Select calendar and add events
    calendar_sync.select_calendar()
    added_events = calendar_sync.add_events_from_csv(csv_path)
    print(f"\nSuccessfully added {len(added_events)} events to the selected calendar")

if __name__ == '__main__':
    main()

import os
import json
import pandas as pd
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
        creds = None
        SCOPES = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/drive'  # Add Drive scope
        ]
        
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, 
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return build('calendar', 'v3', credentials=creds)

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
            print("No calendar selected. Please select a calendar first.")
            self.select_calendar()

        try:
            df = pd.read_csv(csv_path, 
                           quoting=1,
                           doublequote=True,
                           escapechar=None,
                           encoding='utf-8',
                           on_bad_lines='skip')
        except Exception as e:
            print(f"Error reading CSV: {str(e)}")
            return []

        df = df[df['Status'] == 'approved']
        if df.empty:
            print("No approved events found in the CSV file.")
            return []

        added_event_ids = []
        
        for _, row in df.iterrows():
            try:
                print(f"\nProcessing event: {row['eventName']}")
                
                # Get scraped data if available
                event_data = self.scraped_data.get(row['eventURL'], {})
                
                location = f"{row['eventVenueName']}, {row['eventAddress']}, {row['eventCity']}"
                
                # Create HTML-formatted description
                description = f"""
<html>
<body>
<p><a href="{row['eventURL']}"><b>RSVP</b></a></p>
<br>
{row['event_description']}

<hr>
<p><b>Event Details:</b></p>
<ul>
    <li>🏢 Venue: <a href="{row['eventGoogleMaps']}">{row['eventVenueName']}</a></li>
    <li>📍 Address: {row['eventAddress']}, {row['eventCity']}</li>
    <li>👥 Organized by: {row['groupName']}</li>
</ul>

</body>
</html>"""
                
                # Set event time from scraped data or default
                if event_data:
                    if event_data.get('start_datetime'):
                        start_time = parser.parse(event_data['start_datetime'])
                        print(f"Using scraped start time: {start_time}")
                        
                        if event_data.get('end_datetime'):
                            end_time = parser.parse(event_data['end_datetime'])
                            print(f"Using scraped end time: {end_time}")
                        else:
                            # If no end time, default to 2 hours after start
                            end_time = start_time + timedelta(hours=2)
                            print(f"Using default end time: {end_time}")
                    else:
                        # No start time found, use default
                        start_time = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
                        end_time = start_time + timedelta(hours=2)
                        print("Using default event times")
                else:
                    # No scraped data, use default
                    start_time = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
                    end_time = start_time + timedelta(hours=2)
                    print("Using default event times")
                
                event = {
                    'summary': row['eventName'].strip(),
                    'location': location,
                    'description': description,
                    'start': {
                        'dateTime': start_time.isoformat(),
                        'timeZone': 'America/Chicago',
                    },
                    'end': {
                        'dateTime': end_time.isoformat(),
                        'timeZone': 'America/Chicago',
                    },
                    'source': {
                        'url': row['eventURL'],
                        'title': 'Chicago Tech Events'
                    }
                }

                # Handle image attachment if available
                if event_data and event_data.get('image_url'):
                    image_url = event_data['image_url']
                    file_id, web_view_link = self.drive_helper.upload_image_from_url(
                        image_url, 
                        row['eventName']
                    )
                    
                    if file_id:
                        # Add attachment to event
                        event['attachments'] = [{
                            'fileUrl': web_view_link,
                            'title': f"Event image for {row['eventName']}",
                            'mimeType': 'image/jpeg',  # Default to JPEG
                            'iconLink': 'https://drive-thirdparty.googleusercontent.com/16/type/image/jpeg'
                        }]
                        
                        # Add image preview in description
                        description += f'\n<br><img src="{web_view_link}" style="max-width:100%;">'
                
                created_event = self.service.events().insert(
                    calendarId=self.calendar_id,
                    body=event,
                    supportsAttachments=True  # Required for attachments
                ).execute()
                
                added_event_ids.append(created_event['id'])
                print(f"Added event: {row['eventName']}")
            except Exception as e:
                print(f"Failed to add event {row['eventName']}: {str(e)}")
                continue
        
        return added_event_ids

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

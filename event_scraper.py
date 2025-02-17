import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import datetime, timedelta
from urllib.parse import urljoin
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path

class EventScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_meetup_event(self, url):
        """Scrape event details from Meetup.com"""
        try:
            print(f"\nDebug: Scraping Meetup URL: {url}")
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find event times
            start_time = None
            end_time = None
            
            # Look for time elements
            time_elements = soup.find_all('time')
            print(f"Debug: Found {len(time_elements)} time elements")
            
            for time_elem in time_elements:
                datetime_str = time_elem.get('datetime')
                text_content = time_elem.get_text(strip=True)
                print(f"Debug: Time element: {time_elem}")
                print(f"Debug: DateTime attribute: {datetime_str}")
                print(f"Debug: Text content: {text_content}")
                print(f"Debug: Previous sibling: {time_elem.previous_sibling}")
                
                if datetime_str:
                    try:
                        # Parse the datetime attribute for start time
                        start_time = parser.parse(datetime_str)
                        print(f"Debug: Parsed start time: {start_time}")
                        
                        # Look for end time in text content
                        if ' to ' in text_content:
                            # Split on "to" and take the second part
                            end_time_str = text_content.split(' to ')[1]
                            # Remove timezone if present
                            end_time_str = end_time_str.split('CST')[0].strip()
                            end_time_str = end_time_str.split('CDT')[0].strip()
                            
                            try:
                                # Parse the end time string directly
                                end_time = parser.parse(end_time_str)
                                print(f"Debug: Parsed end time from text: {end_time}")
                            except Exception as e:
                                print(f"Debug: Error parsing end time: {str(e)}")
                                end_time = start_time + timedelta(hours=2)
                                print(f"Debug: Using default end time: {end_time}")
                        else:
                            # If no end time found in text, use default duration
                            end_time = start_time + timedelta(hours=2)
                            print(f"Debug: No end time in text, using default: {end_time}")
                            
                    except Exception as e:
                        print(f"Debug: Error parsing datetime: {str(e)}")
            
            # Find event image
            image_url = None
            og_image = soup.find('meta', property='og:image')
            if og_image:
                image_url = og_image.get('content')
                print(f"Debug: Found image URL: {image_url}")
            
            return {
                'start_datetime': start_time.isoformat() if start_time else None,
                'end_datetime': end_time.isoformat() if end_time else None,
                'image_url': image_url
            }
        except Exception as e:
            print(f"Error scraping Meetup event: {str(e)}")
            import traceback
            print(f"Debug: Full error traceback:\n{traceback.format_exc()}")
            return None

    def scrape_mhub_event(self, url):
        """Scrape event details from mHUB website"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find event times
            start_time = None
            end_time = None
            
            # Look for time elements or divs with date/time information
            time_element = soup.find('div', class_='event-date') or soup.find('time')
            if time_element:
                text_content = time_element.get_text()
                
                # Try to find start and end times in the text
                # Common formats: "Start: 2pm End: 4pm" or "2pm - 4pm" or "2pm to 4pm"
                try:
                    if ' - ' in text_content:
                        start_str, end_str = text_content.split(' - ')
                    elif ' to ' in text_content:
                        start_str, end_str = text_content.split(' to ')
                    elif 'Start:' in text_content and 'End:' in text_content:
                        start_str = text_content.split('Start:')[1].split('End:')[0]
                        end_str = text_content.split('End:')[1]
                    else:
                        # If no clear end time indicator, just parse what we have as start time
                        start_time = parser.parse(text_content, fuzzy=True)
                        end_time = start_time + timedelta(hours=2)  # Default 2 hour duration
                        
                    if not start_time and not end_time:
                        start_time = parser.parse(start_str, fuzzy=True)
                        end_time = parser.parse(end_str, fuzzy=True)
                except:
                    # If parsing fails, try to find any datetime in the text
                    try:
                        start_time = parser.parse(text_content, fuzzy=True)
                        end_time = start_time + timedelta(hours=2)  # Default 2 hour duration
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
            
            return {
                'start_datetime': start_time.isoformat() if start_time else None,
                'end_datetime': end_time.isoformat() if end_time else None,
                'image_url': image_url
            }
        except Exception as e:
            print(f"Error scraping mHUB event: {str(e)}")
            return None

    def scrape_luma_event(self, url):
        """Scrape event details from Lu.ma"""
        try:
            print(f"\nDebug: Scraping Lu.ma URL: {url}")
            
            # Add custom headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://lu.ma/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print("Debug: Successfully fetched Lu.ma page")
            
            # Find event times using meta tags
            start_time = None
            end_time = None
            
            # Look for event time in meta tags
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                if meta.get('property') == 'event:start_time':
                    start_time = parser.parse(meta.get('content'))
                    print(f"Debug: Found start time: {start_time}")
                elif meta.get('property') == 'event:end_time':
                    end_time = parser.parse(meta.get('content'))
                    print(f"Debug: Found end time: {end_time}")
            
            # If no meta tags, try to find time in the page content
            if not start_time:
                print("Debug: Looking for time in page content")
                # Look for elements with datetime attributes or specific classes
                time_elements = soup.find_all(['time', 'div'], class_=lambda x: x and ('date' in x.lower() or 'time' in x.lower()))
                for elem in time_elements:
                    print(f"Debug: Found time element: {elem}")
                    try:
                        if elem.get('datetime'):
                            start_time = parser.parse(elem['datetime'])
                            print(f"Debug: Parsed datetime attribute: {start_time}")
                            break
                        else:
                            # Try to parse text content
                            text = elem.get_text(strip=True)
                            if text:
                                print(f"Debug: Trying to parse text: {text}")
                                # Look for patterns like "Feb 10, 2025 6:00 PM - 8:00 PM"
                                if ' - ' in text:
                                    start_str, end_str = text.split(' - ')
                                    start_time = parser.parse(start_str)
                                    # For end time, combine the date from start with the end time
                                    if ':' in end_str:  # Make sure it looks like a time
                                        end_time = parser.parse(f"{start_time.date()} {end_str}")
                                    print(f"Debug: Parsed start: {start_time}, end: {end_time}")
                                    break
                                else:
                                    start_time = parser.parse(text)
                                    print(f"Debug: Parsed single time: {start_time}")
                                    break
                    except Exception as e:
                        print(f"Debug: Error parsing time element: {str(e)}")
                        continue
            
            # If we found a start time but no end time, default to 2 hours
            if start_time and not end_time:
                end_time = start_time + timedelta(hours=2)
                print(f"Debug: Using default 2-hour duration, end time: {end_time}")
            
            # Find event image
            image_url = None
            # Try og:image first
            og_image = soup.find('meta', property='og:image')
            if og_image:
                image_url = og_image.get('content')
                print(f"Debug: Found og:image: {image_url}")
            
            # If no og:image, look for event cover image
            if not image_url:
                img_elements = soup.find_all('img', class_=lambda x: x and ('cover' in x.lower() or 'hero' in x.lower()))
                if img_elements:
                    image_url = img_elements[0].get('src')
                    if image_url and not image_url.startswith('http'):
                        image_url = urljoin(url, image_url)
                    print(f"Debug: Found cover image: {image_url}")
            
            return {
                'start_datetime': start_time.isoformat() if start_time else None,
                'end_datetime': end_time.isoformat() if end_time else None,
                'image_url': image_url
            }
            
        except Exception as e:
            print(f"Error scraping Lu.ma event: {str(e)}")
            import traceback
            print(f"Debug: Full error traceback:\n{traceback.format_exc()}")
            return None

    def get_event_details(self, url):
        """Get event details based on URL"""
        if 'meetup.com' in url:
            return self.scrape_meetup_event(url)
        elif 'mhubchicago.com' in url:
            return self.scrape_mhub_event(url)
        elif 'lu.ma' in url:
            return self.scrape_luma_event(url)
        else:
            print(f"Unsupported event URL format: {url}")
            return None

    def process_and_add_event(self, event_url, calendar_service):
        """
        Process an event URL and add it to Google Calendar
        
        Args:
            event_url (str): URL of the event to scrape
            calendar_service (googleapiclient.discovery.Resource): Google Calendar service object
        
        Returns:
            dict: Processed event details or None if scraping fails
        """
        try:
            # Scrape event details
            event_details = self.get_event_details(event_url)
            if not event_details:
                print(f"Could not extract event details from {event_url}")
                return None
            
            start_time = parser.parse(event_details['start_datetime'])
            end_time = parser.parse(event_details['end_datetime'])
            image_url = event_details['image_url']
            
            # Prepare event details for Google Calendar
            event = {
                'summary': f'Event from {event_url}',
                'location': event_url,
                'description': f'Event scraped from {event_url}\n\nImage: {image_url or "No image available"}',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/Chicago',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/Chicago',
                },
            }
            
            # Add event to Google Calendar
            created_event = calendar_service.events().insert(
                calendarId='primary', 
                body=event
            ).execute()
            
            print(f'Event created: {created_event.get("htmlLink")}')
            
            return {
                'event_url': event_url,
                'event_time': start_time,
                'calendar_link': created_event.get('htmlLink'),
                'image_url': image_url
            }
        
        except Exception as e:
            print(f"Error processing event from {event_url}: {str(e)}")
            return None

def scrape_events_from_csv(csv_path, output_path):
    """
    Scrape details for all events in the CSV and save to a JSON file
    
    Args:
        csv_path: Path to the CSV file with events
        output_path: Path to save the scraped data JSON
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_path, 
                        quoting=1,
                        doublequote=True,
                        escapechar=None,
                        encoding='utf-8',
                        on_bad_lines='skip')
        
        # Filter for approved events and drop rows with missing eventURL
        df = df[df['Status'] == 'approved'].copy()
        df = df.dropna(subset=['eventURL'])
        
        scraper = EventScraper()
        scraped_data = {}
        
        print(f"Found {len(df)} approved events to scrape")
        
        for _, row in df.iterrows():
            try:
                event_url = str(row['eventURL']).strip()
                event_name = str(row.get('eventName', 'Unknown Event')).strip()
                
                if not event_url or pd.isna(event_url):
                    print(f"\nSkipping event '{event_name}': No URL provided")
                    continue
                    
                print(f"\nScraping: {event_name}")
                
                event_details = scraper.get_event_details(event_url)
                if event_details:
                    scraped_data[event_url] = event_details
                    print("Successfully scraped event details")
                else:
                    print("Failed to scrape event details")
            except Exception as e:
                print(f"Error processing event: {str(e)}")
                continue
        
        # Save to JSON file
        if scraped_data:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(scraped_data, f, indent=2, ensure_ascii=False)
            print(f"\nScraped data saved to {output_path}")
            print(f"Successfully scraped {len(scraped_data)} events")
        else:
            print("\nNo event data was scraped successfully")
        
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        # Print more detailed error information
        import traceback
        print(traceback.format_exc())

def main():
    csv_path = 'Table2.csv'
    output_path = 'scraped_events.json'
    
    # Authenticate with Google Calendar API
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    service = build('calendar', 'v3', credentials=creds)
    
    scraper = EventScraper()
    scrape_events_from_csv(csv_path, output_path)
    
    # Process and add events to Google Calendar
    with open(output_path, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    for event_url, event_details in scraped_data.items():
        scraper.process_and_add_event(event_url, service)

if __name__ == '__main__':
    main()

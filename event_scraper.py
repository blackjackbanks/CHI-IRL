import requests
import requests_cache
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import datetime, timedelta
import json
import os
import csv
from urllib.parse import urljoin
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

class EventScraper:
    def __init__(self):
        # Use cached session to reduce unnecessary requests
        self.session = requests_cache.CachedSession('event_cache', expire_after=60*60*24*7)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_luma_event(self, url):
        """Scrape Lu.Ma event details"""
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for LD+JSON script tag
            script = soup.find('script', {'type': 'application/ld+json'})
            if not script:
                print(f"No LD+JSON script found for {url}")
                return None
            
            json_data = json.loads(script.string)
            
            return {
                'title': json_data.get('name', 'Unnamed Event'),
                'start_datetime': parser.parse(json_data.get('startDate')),
                'end_datetime': parser.parse(json_data.get('endDate')),
                'location': json_data.get('location', {}).get('name', ''),
                'description': f'<a href="{url}">RSVP</a>\n\n\n{json_data.get("description", "")}',
                'image_url': json_data.get('image', '')
            }
        except Exception as e:
            print(f"Error scraping Lu.Ma event {url}: {e}")
            return None

    def scrape_meetup_event(self, url):
        """Scrape Meetup.com event details"""
        try:
            response = self.session.get(url)
            
            # Check if response is successful
            if response.status_code != 200:
                print(f"Failed to fetch URL. Status code: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for Next.js data script
            next_data_script = soup.find('script', id='__NEXT_DATA__')
            if not next_data_script:
                print(f"No Next.js data found for {url}")
                return None
            
            # Safely parse JSON
            try:
                json_data = json.loads(next_data_script.string)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON for {url}")
                return None
            
            # Check if required keys exist
            if 'props' not in json_data or 'pageProps' not in json_data['props']:
                print(f"Unexpected JSON structure for {url}")
                return None
            
            apollo_state = json_data['props']['pageProps'].get('__APOLLO_STATE__', {})
            
            # Find event key
            event_key = next((key for key in apollo_state.keys() if 'Event:' in key), None)
            if not event_key:
                print(f"No event data found for {url}")
                return None
            
            event = apollo_state[event_key]
            
            # Extract datetime from multiple possible sources
            start_time = None
            end_time = None
            
            # Try parsing datetime from event data
            datetime_sources = [
                event.get('dateTime'),  # First choice
                event.get('startTime'),  # Fallback 1
                next((item.get('dateTime') for item in apollo_state.values() if isinstance(item, dict) and 'dateTime' in item), None)  # Fallback 2
            ]
            
            # Try parsing start time
            for datetime_str in datetime_sources:
                if datetime_str:
                    try:
                        start_time = parser.parse(datetime_str)
                        break
                    except Exception as e:
                        print(f"Failed to parse start datetime from {datetime_str}: {e}")
            
            # Try parsing end time
            end_time_sources = [
                event.get('endTime'),  # First choice
                next((item.get('endTime') for item in apollo_state.values() if isinstance(item, dict) and 'endTime' in item), None)  # Fallback
            ]
            
            for end_datetime_str in end_time_sources:
                if end_datetime_str:
                    try:
                        end_time = parser.parse(end_datetime_str)
                        break
                    except Exception as e:
                        print(f"Failed to parse end datetime from {end_datetime_str}: {e}")
            
            # Fallback: look for datetime in page content
            if not start_time:
                time_container = soup.find('div', {'data-testid': 'event-when-display'})
                if time_container:
                    time_text = time_container.get_text(strip=True)
                    try:
                        # Example format: "Tuesday, February 20, 2024 7:00 AM to 8:30 AM CST"
                        if ' to ' in time_text:
                            date_part = time_text.split(',')[1:3]  # Get the date parts
                            date_str = ''.join(date_part).strip()
                            times = time_text.split(' to ')
                            
                            # Parse start time
                            start_str = f"{date_str} {times[0].split()[-2]} {times[0].split()[-1]}"
                            start_time = parser.parse(start_str)
                            
                            # Parse end time
                            end_str = f"{date_str} {times[1].split()[0]} {times[1].split()[1]}"
                            end_time = parser.parse(end_str)
                        else:
                            # If no end time, use start time + 2 hours
                            start_time = parser.parse(time_text)
                            end_time = start_time + timedelta(hours=2)
                    except Exception as e:
                        print(f"Failed to parse time from container: {e}")
            
            # If no start time found, return None
            if not start_time:
                print("Could not extract datetime for the event")
                return None
            
            # If no end time, default to 2 hours after start
            if not end_time:
                end_time = start_time + timedelta(hours=2)
            
            # Find location
            location = event.get('venue', {}).get('name', '')
            if not location:
                location_elem = soup.find('div', {'data-testid': 'venue-display'})
                if location_elem:
                    location = location_elem.get_text(strip=True)
            
            # Find description
            description = event.get('description', '')
            if not description:
                description_elem = soup.find('div', {'data-testid': 'event-description'})
                if description_elem:
                    description = description_elem.get_text(strip=True)
            
            # Prepend RSVP link to description with HTML link and two line breaks
            rsvp_link = f'<a href="{url}">RSVP</a>\n\n\n{description}'
            
            return {
                'title': event.get('title', 'Unnamed Event'),
                'start_datetime': start_time,
                'end_datetime': end_time,
                'location': location,
                'description': rsvp_link,
                'image_url': event.get('image', '')
            }
        except Exception as e:
            print(f"Error scraping Meetup event {url}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def scrape_mhub_event(self, url):
        """Scrape mHUB event details"""
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Logging for title extraction
            print("\n--- mHUB Title Extraction Debug ---")
            
            # Method 1: Try to find title in page title
            page_title = soup.title.string if soup.title else ''
            print(f"Page Title: {page_title}")
            
            # Method 2: Look for main heading in event details
            event_details = soup.find('div', class_='event-details-col')
            if not event_details:
                print(f"No event details found for {url}")
                return None
            
            # Try multiple ways to extract the title
            title_candidates = []
            
            # Method 3: Look for h1 or h2 headings in event details
            headings = event_details.find_all(['h1', 'h2'])
            for heading in headings:
                heading_text = heading.get_text(strip=True)
                if heading_text and len(heading_text) > 10:  # Avoid very short titles
                    title_candidates.append(heading_text)
                    print(f"Heading Title Candidate: {heading_text}")
            
            # Method 4: Look for meta title tag
            meta_title = soup.find('meta', property='og:title')
            if meta_title and meta_title.get('content'):
                title_candidates.append(meta_title['content'])
                print(f"Meta Title Candidate: {meta_title['content']}")
            
            # Method 5: Extract title from URL
            url_title = url.split('/')[-1].replace('-', ' ').replace('---', ' ').title()
            title_candidates.append(url_title)
            print(f"URL Title Candidate: {url_title}")
            
            # Select the best title
            def title_score(title):
                """Score title based on length and specificity"""
                score = 0
                if 'event' in title.lower():
                    score += 10
                score += len(title.split())  # Prefer longer titles
                return score
            
            # Sort and select the best title
            title_candidates = [t for t in title_candidates if t]  # Remove empty strings
            if title_candidates:
                event_title = max(title_candidates, key=title_score)
                print(f"Selected Title: {event_title}")
            else:
                event_title = 'mHUB Event'
                print("No suitable title found. Using default.")
            
            # Logging for image extraction
            print("\n--- mHUB Image Extraction Debug ---")
            
            # Try multiple methods to find event image
            image_urls = []
            
            # Method 1: Look for og:image meta tag
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                print(f"Found og:image: {og_image['content']}")
                image_urls.append(og_image['content'])
            
            # Method 2: Look for event image in img tags
            event_images = soup.find_all('img', class_=lambda x: x and ('event' in x.lower() or 'image' in x.lower()))
            for img in event_images:
                img_src = img.get('src') or img.get('data-src')
                if img_src:
                    print(f"Found img tag image: {img_src}")
                    image_urls.append(img_src)
            
            # Method 3: Look for any large images in the event details
            if event_details:
                large_images = event_details.find_all('img', src=True, width=lambda x: x and int(x) > 300)
                for img in large_images:
                    print(f"Found large image in event details: {img['src']}")
                    image_urls.append(img['src'])
            
            # Method 4: Check for background images in style attributes
            style_images = soup.find_all(style=lambda value: value and 'background-image' in value)
            for elem in style_images:
                import re
                bg_image_match = re.search(r'background-image:\s*url\([\'"]?([^\'"]+)[\'"]?\)', elem['style'])
                if bg_image_match:
                    bg_image_url = bg_image_match.group(1)
                    print(f"Found background image: {bg_image_url}")
                    image_urls.append(bg_image_url)
            
            # Remove duplicates while preserving order
            image_urls = list(dict.fromkeys(image_urls))
            
            # Log final image URLs
            print(f"Total image URLs found: {len(image_urls)}")
            for url in image_urls:
                print(f"Potential Image URL: {url}")
            
            # Select the first image URL if available
            image_url = image_urls[0] if image_urls else ''
            
            # Extract venue details
            venue_name = event_details.find('h4', string='Venue').find_next('p').text.strip()
            if venue_name in ['mHUB 1623 W Fulton St', 'mHUB Classroom']:
                venue_name = 'mHUB'
            
            # Extract location
            location_elem = event_details.find('h4', string='Location').find_next('p')
            location = location_elem.text.strip()
            
            # Extract date and time with more robust parsing
            date_time_elem = event_details.find('h4', string='Date and Time').find_next('p')
            date_time_text = date_time_elem.text.strip()
            
            # Custom parsing for mHUB date format (e.g., "02/18/25 @ 6:00 PM")
            try:
                # Split the date and time
                date_str, time_str = date_time_text.split('@')
                date_str = date_str.strip()
                time_str = time_str.strip()
                
                # Parse date with custom format
                parsed_date = datetime.strptime(date_str, '%m/%d/%y')
                
                # Parse time
                parsed_time = datetime.strptime(time_str, '%I:%M %p').time()
                
                # Combine date and time
                start_time = datetime.combine(parsed_date.date(), parsed_time)
                
                # Set timezone to Chicago
                from dateutil.tz import gettz
                start_time = start_time.replace(tzinfo=gettz('America/Chicago'))
                
                # Default end time to 2 hours after start
                end_time = start_time + timedelta(hours=2)
            
            except Exception as e:
                print(f"Failed to parse datetime from {date_time_text}: {e}")
                return None
            
            # Extract description
            description_tag = event_details.find('p', id='evDescription')
            description = ' '.join(
                elem.get_text(strip=True) 
                for elem in description_tag.next_siblings 
                if elem.name == 'p'
            )
            
            return {
                'title': event_title,
                'start_datetime': start_time,
                'end_datetime': end_time,
                'location': location,
                'description': f'<a href="{url}">RSVP</a>\n\n\n{description}',
                'image_url': image_url
            }
        except Exception as e:
            print(f"Error scraping mHUB event {url}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_event_details(self, url):
        """Determine scraping method based on URL"""
        if 'lu.ma' in url:
            return self.scrape_luma_event(url)
        elif 'meetup.com' in url:
            return self.scrape_meetup_event(url)
        elif 'mhubchicago.com' in url:
            return self.scrape_mhub_event(url)
        else:
            print(f"Unsupported event source: {url}")
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
            # Log the start of event processing
            print(f"\n--- Processing Event URL: {event_url} ---", flush=True)
            
            # Scrape event details
            event_details = self.get_event_details(event_url)
            
            if not event_details:
                print(f"Failed to extract event details from {event_url}", flush=True)
                return None
            
            # Normalize image URL (handle list or single URL)
            image_url = event_details.get('image_url')
            if isinstance(image_url, list):
                image_url = image_url[0] if image_url else None
            
            # Log scraped event details
            print("Scraped Event Details:", flush=True)
            print(f"Title: {event_details.get('title', 'No Title')}", flush=True)
            print(f"Image URL: {image_url or 'No Image'}", flush=True)
            
            # Check for valid datetime
            start_datetime = event_details.get('start_datetime')
            end_datetime = event_details.get('end_datetime')
            
            # If no datetime found, use a default or skip
            if not start_datetime:
                print(f"No datetime found for event: {event_details.get('title', 'Unnamed Event')}", flush=True)
                return None
            
            # Ensure datetime objects
            if not isinstance(start_datetime, datetime):
                start_datetime = datetime.fromisoformat(str(start_datetime))
            
            if not isinstance(end_datetime, datetime):
                end_datetime = datetime.fromisoformat(str(end_datetime)) if end_datetime else start_datetime + timedelta(hours=2)
            
            # Create calendar event
            event = {
                'summary': event_details.get('title', 'No Title'),
                'location': event_details.get('location', ''),
                'description': event_details.get('description', ''),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/Chicago',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/Chicago',
                },
            }
            
            # Handle event image attachment
            if image_url:
                try:
                    # Import required libraries
                    import requests
                    import base64
                    import mimetypes
                    from googleapiclient.discovery import build
                    from googleapiclient.http import MediaIoBaseUpload
                    import io
                    
                    # Log detailed image download attempt
                    print("\n--- Image Upload Process ---", flush=True)
                    print(f"Attempting to download image from: {image_url}", flush=True)
                    
                    # Download image with detailed logging
                    try:
                        response = requests.get(image_url, timeout=10)
                        print(f"Download response status: {response.status_code}", flush=True)
                    except requests.RequestException as req_err:
                        print(f"Request error during image download: {req_err}", flush=True)
                        raise
                    
                    # Check if download was successful
                    if response.status_code == 200:
                        # Detailed logging of image content
                        print(f"Downloaded image size: {len(response.content)} bytes", flush=True)
                        
                        # Guess mime type
                        mime_type, _ = mimetypes.guess_type(image_url)
                        if not mime_type:
                            mime_type = 'image/jpeg'  # Default to JPEG
                        print(f"Detected MIME type: {mime_type}", flush=True)
                        
                        # Prepare file for upload
                        file_metadata = {
                            'name': f'event_image_{start_datetime.strftime("%Y%m%d")}',
                            'mimeType': mime_type
                        }
                        
                        # Create file-like object for upload
                        file_bytes = io.BytesIO(response.content)
                        media = MediaIoBaseUpload(
                            file_bytes, 
                            mimetype=mime_type, 
                            resumable=True
                        )
                        
                        # Use Google Drive API to create the file
                        drive_service = build('drive', 'v3', credentials=calendar_service._http.credentials)
                        
                        print("Attempting to upload file to Google Drive...", flush=True)
                        try:
                            # Create the file
                            file = drive_service.files().create(
                                body=file_metadata, 
                                media_body=media, 
                                fields='id,webViewLink'
                            ).execute()
                            
                            print(f"Successfully uploaded file to Google Drive. File ID: {file.get('id')}", flush=True)
                            
                            # Make the file publicly accessible
                            drive_service.permissions().create(
                                fileId=file['id'], 
                                body={'type': 'anyone', 'role': 'reader'}
                            ).execute()
                            
                            # Get the web view link
                            web_link = file.get('webViewLink', image_url)
                            print(f"Web view link: {web_link}", flush=True)
                            
                            # Add the file link to the event description
                            event['description'] += f"\n\nEvent Image: {web_link}"
                        
                        except Exception as drive_err:
                            print(f"Error uploading to Google Drive: {drive_err}", flush=True)
                            import traceback
                            traceback.print_exc()
                            raise
                    
                    else:
                        print(f"Failed to download image. Status code: {response.status_code}", flush=True)
                
                except Exception as img_error:
                    print(f"Comprehensive error handling event image: {img_error}", flush=True)
                    import traceback
                    traceback.print_exc()
            
            # Insert event into calendar
            created_event = calendar_service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            print(f"Successfully created calendar event: {created_event['id']}", flush=True)
            print(f"Event link: {created_event.get('htmlLink', 'No link available')}", flush=True)
            
            return event_details
            
        except Exception as e:
            import traceback
            print(f"Error processing event {event_url}: {str(e)}", flush=True)
            print("Traceback:", flush=True)
            print(traceback.format_exc(), flush=True)
            return None

def scrape_events_from_csv(csv_path, output_path):
    """
    Scrape details for all events in the CSV and save to a JSON file
    
    Args:
        csv_path: Path to the CSV file with events
        output_path: Path to save the scraped data JSON
    """
    try:
        scraped_events = []
        scraper = EventScraper()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                event_url = row.get('Event URL', '').strip()
                if not event_url or event_url.lower() in ['', 'nan', 'none']:
                    continue
                
                try:
                    event_details = scraper.get_event_details(event_url)
                    if event_details:
                        scraped_events.append(event_details)
                except Exception as e:
                    print(f"Error scraping event {event_url}: {str(e)}")
                    continue
        
        # Save scraped events to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scraped_events, f, indent=4, default=str)
            
        print(f"Successfully scraped {len(scraped_events)} events")
        return scraped_events
        
    except Exception as e:
        print(f"Error reading CSV or saving JSON: {str(e)}")
        return None

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
    
    scrape_events_from_csv(csv_path, output_path)
    
    # Process and add events to Google Calendar
    with open(output_path, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    for event_url, event_details in scraped_data.items():
        EventScraper().process_and_add_event(event_url, service)

if __name__ == '__main__':
    main()

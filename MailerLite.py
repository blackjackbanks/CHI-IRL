import os
import pickle
import datetime
import json
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mailerlite_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Load environment variables from .env file
load_dotenv()

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# MailerLite API key (store this in .env file)
MAILERLITE_API_KEY = os.getenv('MAILERLITE_API_KEY')

class MailerLiteAPI:
    def __init__(self, api_key=None):
        """Initialize the MailerLite API client"""
        self.api_key = api_key or MAILERLITE_API_KEY
        if not self.api_key:
            raise ValueError("MailerLite API key is required. Set it in .env file or pass it to the constructor.")
        
        self.base_url = "https://connect.mailerlite.com/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_campaigns(self, status=None, type=None, page=1, limit=25):
        """
        Get a list of campaigns
        
        Args:
            status (str, optional): Filter by status (draft, sent, etc.)
            type (str, optional): Filter by type (regular, ab, etc.)
            page (int, optional): Page number for pagination
            limit (int, optional): Number of results per page
        
        Returns:
            dict: JSON response with campaign data
        """
        url = f"{self.base_url}/campaigns"
        params = {
            "page": page,
            "limit": limit
        }
        
        if status:
            params["filter[status]"] = status
        
        if type:
            params["filter[type]"] = type
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_campaign(self, campaign_id):
        """
        Get details of a specific campaign
        
        Args:
            campaign_id (str): ID of the campaign
        
        Returns:
            dict: JSON response with campaign data
        """
        url = f"{self.base_url}/campaigns/{campaign_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_campaign_content(self, campaign_id):
        """
        Get the HTML content of a campaign
        
        Args:
            campaign_id (str): ID of the campaign
        
        Returns:
            str: HTML content of the campaign
        """
        try:
            # First get the campaign details
            campaign_data = self.get_campaign(campaign_id)
            
            # Print the structure for debugging
            print(f"Campaign data type: {type(campaign_data)}")
            if isinstance(campaign_data, dict):
                print(f"Campaign data keys: {list(campaign_data.keys())}")
            
            # Extract the HTML content from the campaign data
            # The content might be in different locations depending on the campaign type
            html_content = None
            
            # Safely navigate the response structure
            if isinstance(campaign_data, dict) and 'data' in campaign_data:
                campaign_info = campaign_data['data']
                print(f"Campaign info type: {type(campaign_info)}")
                
                if isinstance(campaign_info, dict) and 'emails' in campaign_info:
                    emails = campaign_info['emails']
                    print(f"Emails type: {type(emails)}")
                    
                    if isinstance(emails, list) and emails:
                        email = emails[0]
                        print(f"Email type: {type(email)}")
                        
                        if isinstance(email, dict):
                            print(f"Email keys: {list(email.keys())}")
                            
                            # Check if there's content in the email
                            if 'content' in email and isinstance(email['content'], dict) and 'html' in email['content']:
                                html_content = email['content']['html']
                                print("Found HTML content in email['content']['html']")
                            
                            # If no HTML content is found but there's a preview URL, we can use that
                            if not html_content and 'preview_url' in email and email['preview_url']:
                                preview_url = email['preview_url']
                                print(f"Using preview URL: {preview_url}")
                                try:
                                    preview_response = requests.get(preview_url)
                                    preview_response.raise_for_status()
                                    html_content = preview_response.text
                                    print("Successfully retrieved HTML from preview URL")
                                except Exception as e:
                                    print(f"Error fetching preview URL: {e}")
            
            if html_content:
                print(f"HTML content found (length: {len(html_content)} characters)")
            else:
                print("No HTML content found")
                
            return html_content
            
        except Exception as e:
            print(f"Error getting campaign content: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_campaign_content(self, campaign_id, output_dir="campaign_exports"):
        """
        Save the HTML content of a campaign to a file
        
        Args:
            campaign_id (str): ID of the campaign
            output_dir (str, optional): Directory to save the file
        
        Returns:
            str: Path to the saved file
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Get campaign details
            campaign_data = self.get_campaign(campaign_id)
            
            # Determine campaign name safely
            campaign_name = f"Campaign_{campaign_id}"
            if isinstance(campaign_data, dict) and 'data' in campaign_data:
                if isinstance(campaign_data['data'], dict) and 'name' in campaign_data['data']:
                    campaign_name = campaign_data['data']['name']
            
            # Sanitize campaign name for filename
            safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in campaign_name)
            
            # Get current date for filename
            date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Get HTML content
            html_content = self.get_campaign_content(campaign_id)
            
            if not html_content:
                print(f"No HTML content found for campaign: {campaign_name}")
                return None
            
            # Save to file
            filename = f"{safe_name}_{date_str}.html"
            file_path = os.path.join(output_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Campaign content saved to: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"Error saving campaign content: {e}")
            import traceback
            traceback.print_exc()
            return None

def list_campaigns(api, status=None, type=None):
    """
    List campaigns and allow user to select one
    
    Args:
        api (MailerLiteAPI): MailerLite API client
        status (str, optional): Filter by status
        type (str, optional): Filter by type
    
    Returns:
        str: ID of the selected campaign
    """
    try:
        # Get campaigns
        campaigns_data = api.get_campaigns(status=status, type=type)
        campaigns = campaigns_data.get('data', [])
        
        if not campaigns:
            print("No campaigns found.")
            return None
        
        # Display campaigns
        print("\nAvailable campaigns:")
        print("-" * 80)
        print(f"{'#':<4} {'Campaign Name':<40} {'Status':<10} {'Type':<10} {'Created At':<20}")
        print("-" * 80)
        
        for i, campaign in enumerate(campaigns):
            print(f"{i+1:<4} {campaign['name'][:38]:<40} {campaign['status']:<10} {campaign['type']:<10} {campaign['created_at']:<20}")
        
        # Ask for selection
        while True:
            try:
                selection = input("\nSelect campaign number (or 'q' to quit): ")
                if selection.lower() == 'q':
                    return None
                
                index = int(selection) - 1
                if 0 <= index < len(campaigns):
                    return campaigns[index]['id']
                else:
                    print(f"Please enter a number between 1 and {len(campaigns)}")
            except ValueError:
                print("Please enter a valid number")
    
    except Exception as e:
        print(f"Error listing campaigns: {e}")
        return None

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
    
    return build('calendar', 'v3', credentials=creds)

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

def get_this_weeks_events(service, calendar_id='primary'):
    """Get events for the current week from Google Calendar"""
    # Calculate start and end of current week (Monday to Sunday)
    today = datetime.datetime.now().date()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    
    # Format times for Google Calendar API
    time_min = datetime.datetime.combine(start_of_week, datetime.time.min).isoformat() + 'Z'
    time_max = datetime.datetime.combine(end_of_week, datetime.time.max).isoformat() + 'Z'
    
    logging.info(f"Fetching events from {start_of_week} to {end_of_week}")
    
    # Call the Calendar API
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    if not events:
        logging.info("No events found for this week.")
        return []
    
    logging.info(f"Found {len(events)} events for this week")
    return events

def format_event_for_newsletter(event):
    """Format a Google Calendar event for MailerLite newsletter"""
    # Extract event details
    summary = event.get('summary', 'Unnamed Event')
    
    # Format start time
    start = event.get('start', {})
    if 'dateTime' in start:
        start_time = datetime.datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
        start_formatted = start_time.strftime('%A, %B %d, %Y at %I:%M %p')
    else:
        # All-day event
        start_date = datetime.datetime.fromisoformat(start['date'])
        start_formatted = start_date.strftime('%A, %B %d, %Y (All day)')
    
    # Get location
    location = event.get('location', 'No location specified')
    
    # Get description and clean it up
    description = event.get('description', '')
    # Remove HTML tags if present
    description = description.replace('<br>', '\n').replace('&nbsp;', ' ')
    
    # Get event URL if available
    event_url = None
    for link in event.get('attachments', []):
        if link.get('title') == 'Event Link' or 'url' in link.get('title', '').lower():
            event_url = link.get('fileUrl')
            break
    
    # Check if there's a URL in the description
    if not event_url and description:
        import re
        url_match = re.search(r'https?://\S+', description)
        if url_match:
            event_url = url_match.group(0)
    
    # Format HTML for MailerLite
    html_content = f"""
    <div class="event-card" style="margin-bottom: 20px; border: 1px solid #e0e0e0; border-radius: 5px; padding: 15px;">
        <h3 style="margin-top: 0; color: #333;">{summary}</h3>
        <p style="margin: 5px 0;"><strong>When:</strong> {start_formatted}</p>
        <p style="margin: 5px 0;"><strong>Where:</strong> {location}</p>
    """
    
    if event_url:
        html_content += f'<p style="margin: 10px 0;"><a href="{event_url}" style="background-color: #4CAF50; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; display: inline-block;">Event Details</a></p>'
    
    if description:
        # Limit description length for newsletter
        short_description = description[:200] + '...' if len(description) > 200 else description
        html_content += f'<p style="margin: 10px 0;">{short_description}</p>'
    
    html_content += '</div>'
    
    return html_content

def create_mailerlite_campaign(events, campaign_name=None):
    """Create a MailerLite campaign with the events"""
    if not MAILERLITE_API_KEY:
        logging.error("MailerLite API key not found. Please set the MAILERLITE_API_KEY environment variable.")
        return False
    
    if not events:
        logging.warning("No events to include in the newsletter.")
        return False
    
    # Generate campaign name if not provided
    if not campaign_name:
        today = datetime.datetime.now()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        campaign_name = f"Weekly Events: {start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d, %Y')}"
    
    # Format all events for the newsletter
    events_html = ""
    for event in events:
        events_html += format_event_for_newsletter(event)
    
    # Create the full HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{campaign_name}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <header style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #4CAF50;">{campaign_name}</h1>
            <p>Here are the upcoming events for this week:</p>
        </header>
        
        <div class="events-container">
            {events_html}
        </div>
        
        <footer style="margin-top: 30px; text-align: center; font-size: 0.8em; color: #777;">
            <p>You're receiving this email because you subscribed to our weekly events newsletter.</p>
            <p>To unsubscribe, click the unsubscribe link at the bottom of this email.</p>
        </footer>
    </body>
    </html>
    """
    
    # Prepare the API request to create a campaign
    url = "https://connect.mailerlite.com/api/campaigns"
    headers = {
        "Authorization": f"Bearer {MAILERLITE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Campaign data
    data = {
        "name": campaign_name,
        "type": "regular",
        "subject": campaign_name,
        "from": "your-email@example.com",  # Replace with your email
        "content": {
            "html": html_content
        }
    }
    
    try:
        # Create the campaign
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        campaign_data = response.json()
        logging.info(f"Campaign created successfully: {campaign_data.get('data', {}).get('id')}")
        
        return campaign_data.get('data', {}).get('id')
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error creating MailerLite campaign: {e}")
        if hasattr(e, 'response') and e.response:
            logging.error(f"Response: {e.response.text}")
        return False

def main():
    """Main function to run the Google Calendar to MailerLite sync"""
    # Get Google Calendar service
    service = get_calendar_service()
    
    # Select calendar
    calendar_id = select_calendar(service)
    
    # Get this week's events
    events = get_this_weeks_events(service, calendar_id)
    
    if events:
        # Create MailerLite campaign
        campaign_id = create_mailerlite_campaign(events)
        
        if campaign_id:
            logging.info(f"Newsletter created successfully! Campaign ID: {campaign_id}")
            logging.info("You can now review and send the campaign from your MailerLite dashboard.")
        else:
            logging.error("Failed to create MailerLite campaign.")
    else:
        logging.warning("No events found for this week. No newsletter created.")

def mailerlite_campaign_exporter():
    """Main function to run the MailerLite campaign exporter"""
    try:
        # Initialize API client
        api = MailerLiteAPI()
        
        # Show options
        print("\nMailerLite Campaign Exporter")
        print("=" * 50)
        print("1. List all campaigns")
        print("2. List sent campaigns")
        print("3. List draft campaigns")
        print("4. Export campaign by ID")
        print("q. Quit")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            campaign_id = list_campaigns(api)
        elif choice == '2':
            campaign_id = list_campaigns(api, status="sent")
        elif choice == '3':
            campaign_id = list_campaigns(api, status="draft")
        elif choice == '4':
            campaign_id = input("Enter campaign ID: ")
        elif choice.lower() == 'q':
            print("Exiting...")
            return
        else:
            print("Invalid option")
            return
        
        if campaign_id:
            # Save campaign content
            output_dir = input("Enter output directory (default: campaign_exports): ") or "campaign_exports"
            api.save_campaign_content(campaign_id, output_dir)
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
    mailerlite_campaign_exporter()
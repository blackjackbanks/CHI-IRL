from google_calendar_sync import GoogleCalendarSync

def add_luma_events_to_calendar(urls):
    """
    Add Lu.Ma events to Google Calendar
    
    Args:
        urls (list): List of Lu.Ma event URLs
    """
    # Path to your Google OAuth credentials
    credentials_path = 'credentials.json'
    
    # Initialize Google Calendar Sync
    calendar_sync = GoogleCalendarSync(credentials_path)
    
    # Select the calendar you want to add events to
    calendar_sync.select_calendar()
    
    # Add Lu.Ma events
    added_events = calendar_sync.add_luma_events(urls)
    
    print(f"\nAdded {len(added_events)} Lu.Ma events to your calendar!")

if __name__ == '__main__':
    # Example usage
    luma_urls = [
        # Replace these with your actual Lu.Ma event URLs
        'https://lu.ma/example-event-1',
        'https://lu.ma/example-event-2'
    ]
    
    add_luma_events_to_calendar(luma_urls)

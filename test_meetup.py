import sys
from event_scraper import EventScraper

def test_meetup_scraper():
    """Test the Meetup event scraper with a sample URL"""
    # Sample Meetup event URL
    url = "https://www.meetup.com/chicago-react-native-meetup/events/306127251/?recId=12f072c1-d761-4a7e-bc7c-a46b97f5e3fa&recSource=event-search&searchId=b570be3e-a01a-4134-941c-f7b37c0feae6&eventOrigin=find_page$inPerson"
    
    print(f"Processing {url}")
    
    # Initialize scraper
    scraper = EventScraper()
    
    # Get event details
    event_details = scraper.scrape_meetup_event(url)
    
    if event_details:
        print(f"Success: {event_details.get('title', 'No title')}")
        print(f"Start time: {event_details.get('start_datetime')}")
        print(f"End time: {event_details.get('end_datetime')}")
        print(f"Location: {event_details.get('location', 'No location')}")
        print(f"Image URL: {event_details.get('image_url', 'No image')}")
        
        # Print first 100 characters of description
        description = event_details.get('description', 'No description')
        print(f"Description: {description[:100]}...")
        
        print("--------------------------------------------------")
        return True
    else:
        print(f"Failed to scrape event details from {url}")
        return False

if __name__ == "__main__":
    # If URL is provided as command line argument, use it
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"Using provided URL: {url}")
        
        # Initialize scraper
        scraper = EventScraper()
        
        # Get event details
        event_details = scraper.scrape_meetup_event(url)
        
        if event_details:
            print(f"Success: {event_details.get('title', 'No title')}")
            print(f"Start time: {event_details.get('start_datetime')}")
            print(f"End time: {event_details.get('end_datetime')}")
            print(f"Location: {event_details.get('location', 'No location')}")
            print(f"Image URL: {event_details.get('image_url', 'No image')}")
            
            # Print first 100 characters of description
            description = event_details.get('description', 'No description')
            print(f"Description: {description[:100]}...")
            
            print("--------------------------------------------------")
        else:
            print(f"Failed to scrape event details from {url}")
    else:
        # Run the default test
        test_meetup_scraper()

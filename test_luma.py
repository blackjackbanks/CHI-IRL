import sys
from event_scraper import EventScraper

def test_luma_scraper():
    """Test the Lu.Ma event scraper with a sample URL"""
    # Sample Lu.Ma event URL
    url = "https://lu.ma/9x1ss8b2"
    
    print(f"Processing {url}")
    
    # Initialize scraper
    scraper = EventScraper()
    
    # Get event details
    event_details = scraper.scrape_luma_event(url)
    
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
        event_details = scraper.scrape_luma_event(url)
        
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
        test_luma_scraper()

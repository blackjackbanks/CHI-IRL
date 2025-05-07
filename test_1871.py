from event_scraper import EventScraper
from datetime import datetime

def test_1871_scraper():
    scraper = EventScraper()
    # Use a real 1871 event URL
    url = 'https://community.1871.com/events/111913'
    
    print(f'Processing {url}')
    event = scraper.scrape_1871_event(url)
    if event:
        print(f'Success: {event["title"]}')
        print(f'Start time: {event["start_datetime"]}')
        print(f'End time: {event["end_datetime"]}')
        print(f'Location: {event["location"]}')
        print(f'Image URL: {event.get("image_url", "No image found")}')
        print(f'Description: {event["description"][:200]}...')
        print('-' * 50)
    else:
        print('Failed to scrape event')
        print('-' * 50)

if __name__ == '__main__':
    test_1871_scraper()

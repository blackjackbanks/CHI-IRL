from event_scraper import EventScraper
from datetime import datetime

def test_mhub_scraper():
    scraper = EventScraper()
    urls = [
        'https://www.mhubchicago.com/events/build-targeted-lists-and-test-your-value-prop-in-clay-ai-124483',
        'https://www.mhubchicago.com/events/march-happy-hour-130849'
    ]
    
    for url in urls:
        print(f'Processing {url}')
        event = scraper.scrape_mhub_event(url)
        if event:
            print(f'Success: {event["title"]} on {event["start_datetime"].strftime("%Y-%m-%d %H:%M")}')
            print(f'Location: {event["location"]}')
            print(f'Image URL: {event.get("image_url", "No image found")}')
            print('-' * 50)
        else:
            print('Failed to scrape event')
            print('-' * 50)

if __name__ == '__main__':
    test_mhub_scraper()

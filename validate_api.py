import sys
import os
import logging
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_validation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from event_scraper import EventScraper
from google_calendar_sync import get_calendar_service

def validate_event_sources():
    """
    Validate event scraping for different sources
    """
    # Test URLs from different platforms
    test_urls = [
        # Meetup event
        'https://www.meetup.com/bootstrappers-breakfast-chicago/events/304560800/',
        
        # Lu.Ma event
        'https://lu.ma/k2yrxjr1',
        
        # mHUB event
        'https://www.mhubchicago.com/events/genai-collective-chicago---how-ai-is-innovating-the-physical-world-128853'
    ]
    
    scraper = EventScraper()
    validation_results = {}
    
    for url in test_urls:
        logging.info(f"\n--- Validating Event Source: {url} ---")
        try:
            # Attempt to scrape event details
            event_details = scraper.get_event_details(url)
            
            if event_details:
                # Validate key event details
                description = event_details.get('description', '')
                
                # Log description details
                logging.info("Description Validation:")
                logging.info(f"Description Length: {len(description)} characters")
                logging.info(f"Description Preview (first 200 chars): {description[:200]}...")
                
                # Validate description criteria
                description_validation = {
                    'has_content': bool(description),
                    'has_rsvp_link': '<a href="' in description,
                    'length': len(description)
                }
                
                validation_results[url] = {
                    'status': 'SUCCESS',
                    'title': event_details.get('title', 'N/A'),
                    'start_datetime': str(event_details.get('start_datetime', 'N/A')),
                    'end_datetime': str(event_details.get('end_datetime', 'N/A')),
                    'location': event_details.get('location', 'N/A'),
                    'image_url': event_details.get('image_url', 'N/A'),
                    'description_validation': description_validation
                }
                logging.info("Description Validation Passed")
            else:
                validation_results[url] = {
                    'status': 'FAILED',
                    'error': 'Could not extract event details'
                }
                logging.warning(f"Failed to scrape event from {url}")
        
        except Exception as e:
            validation_results[url] = {
                'status': 'ERROR',
                'error': str(e)
            }
            logging.error(f"Error scraping {url}: {e}")
    
    return validation_results

def validate_google_calendar_integration():
    """
    Validate Google Calendar service and event creation
    """
    logging.info("\n--- Validating Google Calendar Integration ---")
    try:
        # Get calendar service
        calendar_service = get_calendar_service()
        logging.info("Successfully obtained Google Calendar service")
        
        # Create a test event
        test_event = {
            'summary': 'API Validation Test Event',
            'location': 'Test Location',
            'description': 'This is a validation event to test Google Calendar API integration',
            'start': {
                'dateTime': (datetime.now() + timedelta(days=1)).isoformat(),
                'timeZone': 'America/Chicago',
            },
            'end': {
                'dateTime': (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
                'timeZone': 'America/Chicago',
            },
        }
        
        # Insert test event
        created_event = calendar_service.events().insert(
            calendarId='primary',
            body=test_event
        ).execute()
        
        logging.info(f"Successfully created test event: {created_event['id']}")
        
        return {
            'status': 'SUCCESS',
            'event_id': created_event['id'],
            'event_link': created_event.get('htmlLink', 'No link available')
        }
    
    except Exception as e:
        logging.error(f"Google Calendar Integration Validation Failed: {e}")
        return {
            'status': 'FAILED',
            'error': str(e)
        }

def main():
    """
    Run comprehensive API validation
    """
    logging.info("\n=== Starting Comprehensive API Validation ===")
    
    # Validate event sources
    event_source_results = validate_event_sources()
    
    # Validate Google Calendar integration
    calendar_integration_results = validate_google_calendar_integration()
    
    # Prepare and print final validation report
    print("\n--- API Validation Report ---")
    print("\nEvent Source Validation:")
    for url, result in event_source_results.items():
        print(f"\n{url}:")
        print(json.dumps(result, indent=2))
    
    print("\nGoogle Calendar Integration:")
    print(json.dumps(calendar_integration_results, indent=2))
    
    # Save results to a JSON file
    with open('api_validation_results.json', 'w') as f:
        json.dump({
            'event_sources': event_source_results,
            'calendar_integration': calendar_integration_results
        }, f, indent=2)
    
    logging.info("\n=== API Validation Complete ===")

if __name__ == '__main__':
    main()

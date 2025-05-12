import os
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime
import argparse

class MailerLiteTemplateGenerator:
    def __init__(self, template_path):
        """Initialize with the path to the template HTML file"""
        self.template_path = template_path
        with open(template_path, 'r', encoding='utf-8') as file:
            self.html_content = file.read()
        self.soup = BeautifulSoup(self.html_content, 'html.parser')
        self.events = []
        
    def extract_events(self):
        """Extract event information from the template"""
        # Find all event blocks
        event_blocks = self.soup.find_all('table', attrs={'align': 'center', 'width': '100%', 'border': '0', 'cellspacing': '0', 'cellpadding': '0'})
        
        for block in event_blocks:
            # Check if this is an event block by looking for specific structure
            image_link = block.find('a', href=True)
            title_link = block.find('h3')
            description = block.find('p')
            
            if image_link and title_link and description:
                # Extract image information
                image_url = None
                image_tag = image_link.find('img')
                if image_tag and 'src' in image_tag.attrs:
                    image_url = image_tag['src']
                
                # Extract title and link
                event_title = title_link.get_text(strip=True)
                event_url = None
                title_a_tag = title_link.find('a', href=True)
                if title_a_tag:
                    event_url = title_a_tag['href']
                
                # Extract description (time and location)
                event_details = description.get_text(strip=True)
                
                # Parse time and location from description
                time_pattern = r'(\d+(?::\d+)?[ap](?:\s*-\s*\d+(?::\d+)?[ap])?)'
                location_pattern = r'\((.*?)\)'
                
                time_match = re.search(time_pattern, event_details)
                location_match = re.search(location_pattern, event_details)
                
                event_time = time_match.group(1) if time_match else ""
                event_location = location_match.group(1) if location_match else ""
                
                # Add to events list
                if event_title and (image_url or event_url):
                    self.events.append({
                        'title': event_title,
                        'url': event_url,
                        'image_url': image_url,
                        'time': event_time,
                        'location': event_location,
                        'full_description': event_details
                    })
        
        return self.events
    
    def save_events_to_json(self, output_path):
        """Save extracted events to a JSON file"""
        if not self.events:
            self.extract_events()
            
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(self.events, file, indent=2)
        
        print(f"Saved {len(self.events)} events to {output_path}")
    
    def generate_template(self, events_data, output_path):
        """Generate a new template with the provided events data"""
        # Load the template as a string for easier manipulation
        with open(self.template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()
        
        # Create a soup object for parsing
        soup = BeautifulSoup(template_content, 'html.parser')
        
        # Find all event blocks
        event_blocks = soup.find_all('table', attrs={'align': 'center', 'width': '100%', 'border': '0', 'cellspacing': '0', 'cellpadding': '0'})
        
        # Keep track of which blocks are event blocks
        event_block_indices = []
        for i, block in enumerate(event_blocks):
            # Check if this is an event block
            if block.find('h3') and block.find('p') and block.find('a', href=True):
                event_block_indices.append(i)
        
        # If we don't have enough event blocks for our data, we'll need to duplicate some
        if len(event_block_indices) > 0 and len(events_data) > len(event_block_indices):
            # Get a sample event block to duplicate
            sample_block_index = event_block_indices[0]
            sample_block = event_blocks[sample_block_index]
            
            # Find the parent container to insert new blocks
            parent = sample_block.parent
            
            # Add more blocks as needed
            for _ in range(len(events_data) - len(event_block_indices)):
                new_block = BeautifulSoup(str(sample_block), 'html.parser')
                parent.append(new_block)
            
            # Refresh our soup and event blocks after modifications
            template_content = str(soup)
            soup = BeautifulSoup(template_content, 'html.parser')
            event_blocks = soup.find_all('table', attrs={'align': 'center', 'width': '100%', 'border': '0', 'cellspacing': '0', 'cellpadding': '0'})
            
            # Update event block indices
            event_block_indices = []
            for i, block in enumerate(event_blocks):
                if block.find('h3') and block.find('p') and block.find('a', href=True):
                    event_block_indices.append(i)
        
        # Now update each event block with our data
        for i, event_data in enumerate(events_data):
            if i < len(event_block_indices):
                block_index = event_block_indices[i]
                block = event_blocks[block_index]
                
                # Update image
                if 'image_url' in event_data and event_data['image_url']:
                    img_tag = block.find('img')
                    if img_tag:
                        img_tag['src'] = event_data['image_url']
                
                # Update links
                if 'url' in event_data and event_data['url']:
                    for a_tag in block.find_all('a', href=True):
                        a_tag['href'] = event_data['url']
                
                # Update title
                if 'title' in event_data and event_data['title']:
                    h3_tag = block.find('h3')
                    if h3_tag:
                        a_tag = h3_tag.find('a')
                        if a_tag:
                            a_tag.string = event_data['title']
                        else:
                            h3_tag.string = event_data['title']
                
                # Update description
                if ('time' in event_data or 'location' in event_data) and block.find('p'):
                    p_tag = block.find('p')
                    description = ""
                    if 'time' in event_data and event_data['time']:
                        description += event_data['time']
                    if 'location' in event_data and event_data['location']:
                        if description:
                            description += f" ({event_data['location']})"
                        else:
                            description += f"({event_data['location']})"
                    p_tag.string = description
        
        # Save the modified template
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(str(soup))
        
        print(f"Generated new template at {output_path}")

def main():
    parser = argparse.ArgumentParser(description='MailerLite Template Generator')
    parser.add_argument('--template', required=True, help='Path to the template HTML file')
    parser.add_argument('--extract', action='store_true', help='Extract events from template')
    parser.add_argument('--json', help='Path to save or load events JSON file')
    parser.add_argument('--generate', help='Path to save the generated template')
    
    args = parser.parse_args()
    
    generator = MailerLiteTemplateGenerator(args.template)
    
    if args.extract:
        events = generator.extract_events()
        print(f"Extracted {len(events)} events from template")
        
        if args.json:
            generator.save_events_to_json(args.json)
    
    if args.generate and args.json:
        # Load events data from JSON
        with open(args.json, 'r', encoding='utf-8') as file:
            events_data = json.load(file)
        
        generator.generate_template(events_data, args.generate)

if __name__ == "__main__":
    main()
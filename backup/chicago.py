import pandas as pd
from meetup import get_meetup_events
from mhub import get_mhub_events
from luma import get_luma_group_events
from common import mark_online_events, upload_to_gsheets, get_gsheet_df, create_event_markdown, create_discord_list, scrape_user_events
from datetime import datetime

organization_df = get_gsheet_df("Organizations")
meetup_groups = organization_df['Meetup'].tolist()
meetup_groups = list(set([x for x in meetup_groups if len(x) > 0]))

luma_groups = organization_df['LuMa'].tolist()
luma_groups = list(set([x for x in luma_groups if len(x) > 0]))

luma_groups

try:
    luma_df = get_luma_group_events(luma_groups, sleep_time=1, verbose=False, debug=True)
except Exception as e:
    print('Failed to get LuMa events')
    print(e)


try:
    meetup_df = get_meetup_events(meetup_groups, sleep_time=2, verbose=True, debug=True)
except Exception as e:
    print('Failed to get Meetup events')
    print(e)
try:
    mhub_df = get_mhub_events()
except Exception as e:
    print('Failed to get MHub events')
    print(e)
try:
    luma_df = get_luma_group_events(luma_groups, sleep_time=1, verbose=False, debug=True)
except Exception as e:
    print('Failed to get LuMa events')
    print(e)




import concurrent.futures

def safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f'Failed to get data from {fn.__name__}')
        print(e)
        return None

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    future_meetup = executor.submit(safe_call, get_meetup_events, meetup_groups, sleep_time=2, verbose=True, debug=True)
    future_mhub = executor.submit(safe_call, get_mhub_events, sleep_time=1, verbose=True, debug=True)
    future_luma = executor.submit(safe_call, get_luma_group_events, luma_groups, sleep_time=1, verbose=False, debug=True)

    meetup_df = future_meetup.result()
    mhub_df = future_mhub.result()
    luma_df = future_luma.result()


luma_users = scrape_user_events(luma_groups)

def scrape_events_and_clean_data():
    import os
    import time
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urlparse
    from datetime import datetime
    import pandas as pd
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    url = 'https://chiirl.com'
    save_dir = 'event_images'
    os.makedirs(save_dir, exist_ok=True)

    def download_image(url, save_dir):
        if not url:
            return ''
        try:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            file_path = os.path.join(save_dir, filename)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return file_path
        except Exception as e:
            print(f"Failed to download image {url}: {e}")
            return ''

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    events = soup.select('div.eapp-events-calendar-grid-item')
    print(f"Found {len(events)} events")

    data = []
    for i, event in enumerate(events, 1):
        try:
            print(f"\nExtracting data for event {i}...")

            # Extract Date
            month_elem = event.select_one('.eapp-events-calendar-date-element-month')
            day_elem = event.select_one('.eapp-events-calendar-date-element.day')

            month = month_elem.text.strip() if month_elem else ''
            day = day_elem.text.strip() if day_elem else ''
            date = f"{month} {day}" if month and day else 'No Date'  # Use 'No Date' if date is missing
            print(f"Date: {date}")

            title_elem = event.select_one('.eapp-events-calendar-grid-item-name')
            title = title_elem.text.strip() if title_elem else ''
            print(f"Title: {title}")

            time_elem = event.select_one('.eapp-events-calendar-time-time')
            time_range = time_elem.text.strip() if time_elem else ''
            print(f"Time Range: {time_range}")

            location_elem = event.select_one('.eapp-events-calendar-location-text')
            location = location_elem.text.strip() if location_elem else ''
            print(f"Location: {location}")

            desc_elem = event.select_one('.eapp-events-calendar-grid-item-description')
            description = desc_elem.get_text(separator=' ', strip=True) if desc_elem else ''
            print(f"Description: {description}")

            img_elem = event.select_one('img')
            image_url = img_elem['src'] if img_elem and img_elem.has_attr('src') else ''
            print(f"Image URL: {image_url}")

            image_path = download_image(image_url, save_dir)
            print(f"Image saved at: {image_path}")

            # Append event data
            data.append({
                'Date': date,
                'Title': title,
                'Time': time_range,
                'Location': location,
                'Description': description,
                'Image URL': image_path
            })

        except Exception as e:
            print(f"❌ Error extracting event {i}: {e}")
            continue

    print(f"\n🖼️  Images saved in: {save_dir}")

    # Transform data
    transformed_data = []
    for event in data:
        if not event.get('Date') or not event.get('Title'):
            print(f"⚠️ Event might be missing important fields: {event}")

        transformed_data.append({
            'eventName': event.get('Title', ''),
            'eventURL': url,
            'eventStartTime': event.get('Date', 'No Date'),  # Set to 'No Date' if missing
            'eventendTime': '',
            'eventVenueName': '',
            'eventAddress': event.get('Location', ''),
            'eventCity': 'Chicago',
            'eventState': 'IL',
            'groupName': '',
            'eventGoogleMaps': '',
            'event_description': event.get('Description', ''),
            'datetimeScraped': pd.Timestamp.now().isoformat()
        })

    columns = [
        'eventName', 'eventURL', 'eventStartTime', 'eventendTime', 'eventVenueName',
        'eventAddress', 'eventCity', 'eventState', 'groupName', 'eventGoogleMaps',
        'event_description', 'datetimeScraped'
    ]
    df = pd.DataFrame(transformed_data, columns=columns)

    return df


# Run it
chiirl = scrape_events_and_clean_data()

# Define the target column structure
target_columns = [
    'eventName', 'eventURL', 'eventStartTime', 'eventendTime', 'eventVenueName',
    'eventAddress', 'eventCity', 'eventState', 'groupName', 'eventGoogleMaps',
    'event_description', 'datetimeScraped'
]

# Function to align a DataFrame to the target columns
def align_columns(df, columns, name="DataFrame"):
    try:
        print(f"\n🧩 Aligning columns for {name}")
        if not isinstance(df, pd.DataFrame):
            raise ValueError(f"{name} is not a valid DataFrame")
        
        # Add missing columns with None
        for col in columns:
            if col not in df.columns:
                print(f"⚠️  {name} missing column: {col} — filling with None")
                df[col] = None

        # Return with ordered columns
        return df[columns]
    except Exception as e:
        print(f"❌ Failed to align {name}: {e}")
        return pd.DataFrame(columns=columns)  # Return empty DataFrame with correct structure

# Align all DataFrames with names for traceability and count rows before/after
def align_and_report(df, name):
    before_rows = len(df) if df is not None else 0
    aligned_df = align_columns(df, target_columns, name)
    after_rows = len(aligned_df) if aligned_df is not None else 0
    print(f"📊 {name}: Rows before = {before_rows}, after alignment = {after_rows}")
    return aligned_df

meetup_df_aligned   = align_and_report(meetup_df, "meetup_df")
mhub_df_aligned     = align_and_report(mhub_df, "mhub_df")
luma_df_aligned     = align_and_report(luma_df, "luma_df")
clean_df_aligned    = align_and_report(luma_users, "luma_users")
clean_df_aligned2   = align_and_report(luma_event, "luma_event")
clean_df_aligned3   = align_and_report(chiirl, "chiirl")

# Attempt to combine everything with fallback
dfs_to_combine = [
    ("meetup_df", meetup_df_aligned),
    ("mhub_df", mhub_df_aligned),
    ("luma_df", luma_df_aligned),
    ("luma_users", clean_df_aligned),
    ("luma_event", clean_df_aligned2),
    ("chiirl", clean_df_aligned3)
]

valid_dfs = []
total_rows_pre_concat = 0
for name, df in dfs_to_combine:
    if df is not None and not df.empty:
        row_count = len(df)
        total_rows_pre_concat += row_count
        print(f"✅ Including {name}: {row_count} rows")
        valid_dfs.append(df)
    else:
        print(f"⚠️ Skipping {name}: DataFrame is None or empty")

# Try concatenating all valid DataFrames
try:
    combined_df = pd.concat(valid_dfs, ignore_index=True)
    print(f"\n✅ Successfully combined {len(valid_dfs)} DataFrames.")
    print(f"🧮 Total rows before concat: {total_rows_pre_concat}, after concat: {len(combined_df)}")
except Exception as e:
    print(f"❌ Error during DataFrame concatenation: {e}")
    combined_df = pd.DataFrame(columns=target_columns)

filtered_df = mark_online_events(combined_df)

#not_chicago_or_online_df
filtered_df

upload_to_gsheets(filtered_df, "Events",['eventURL'], verbose=True)


import pandas as pd
import re
from collections import defaultdict

def categorize_tech_event(event_description):
    if pd.isna(event_description):
        return "Other Tech"
        
    desc = str(event_description).lower()
    
    categories = {
        'AI/ML': r'\b(ai\b|artificial\s*intelligence|machine\s*learning|ml\b|deep\s*learning|llm|generative\s*ai|chatgpt|gpt|neural\s*network|computer\s*vision|nlp|tensorflow|pytorch)\b',
        'Web3/Blockchain': r'\b(web3|blockchain|crypto\w*|solidity|smart\s*contract|ethereum|defi|nft|dao|dapp|ipfs|filecoin)\b',
        'Cloud/DevOps': r'\b(cloud|aws|azure|gcp|kubernetes|k8s|docker|devops|sre|infrastructure\s*as\s*code|iac|terraform|ansible|jenkins)\b',
        'Programming': r'\b(python|ruby|javascript|java|c\+\+|rust|golang|php|swift|kotlin|typescript|dart|rlang|programming|coding)\b',
        'Cybersecurity': r'\b(cybersecurity|infosec|pentest|red\s*team|blue\s*team|ctf|ethical\s*hacking|owasp|vulnerability|exploit|malware)\b',
        'Web Dev': r'\b(web\s*dev|frontend|backend|fullstack|html|css|node\.?js|django|rails|laravel|spring|angular|vue|svelte|graphql)\b',
        'Data': r'\b(data\s*science|data\s*engineering|analytics|big\s*data|sql|nosql|postgres|mysql|mongodb|spark|hadoop|databricks)\b',
        'Mobile': r'\b(mobile|android|ios|react\s*native|flutter|xamarin|kotlin\s*multiplatform|swiftui|jetpack\s*compose)\b',
        'Hardware/IoT': r'\b(hardware|electronics|iot|arduino|raspberry\s*pi|3d\s*printing|cnc|robotics|vr|ar|sensor|actuator)\b',
    }
    
    for category, pattern in categories.items():
        if re.search(pattern, desc, re.IGNORECASE):
            return category
    return 'Other Tech'

# Main processing function
def process_tech_events(df):
    # Categorize all events, whether tech or not
    df = df.copy()
    df['tech_category'] = df['event_description'].apply(categorize_tech_event)
    return df

# Usage example
tech_events_df = process_tech_events(combined_df)

# Display results
print(f"Processed {len(tech_events_df)} total events")
print("\nTech Categories Breakdown:")
print(tech_events_df['tech_category'].value_counts())


import pandas as pd
import markdown
from dateutil import parser

def create_event_markdown(event_df, name='Events'):
    # Safely parse dates
    def safe_parse_date(x):
        if pd.isnull(x) or str(x).strip() == "":
            return pd.NaT
        try:
            return parser.parse(str(x))
        except (parser.ParserError, ValueError, TypeError):
            return pd.NaT

    event_df = event_df.copy()

    # Parse eventStartTime safely
    event_df['eventStartTime'] = event_df['eventStartTime'].apply(safe_parse_date)

    # Sort and keep only future events
    event_df = event_df.sort_values(by='eventStartTime', ascending=True)
    now = pd.Timestamp.now()
    event_df = event_df[event_df['eventStartTime'].isna() | (event_df['eventStartTime'] >= now)]

    # Format dates safely: if NaT, put "Date TBD"
    event_df['formatted_date'] = event_df['eventStartTime'].apply(
        lambda x: x.strftime('%A, %B %d @ %I:%M%p') if pd.notnull(x) else 'Date TBD'
    )

    # Deduplicate
    event_df = event_df.drop_duplicates(subset='eventName', keep='first')
    event_df = event_df.drop_duplicates(subset=['eventStartTime', 'eventVenueName'], keep='first')

    event_string = ''

    # Build Markdown string
    for index, row in event_df.iterrows():
        event_name = str(row.get('eventName', 'Unnamed Event')).strip() or 'Unnamed Event'
        event_url = str(row.get('eventURL', '#')).strip() or '#'
        group_name = str(row.get('groupName', 'Unknown Organization')).strip() or 'Unknown Organization'
        formatted_date = row.get('formatted_date', 'Date TBD') or 'Date TBD'
        venue_name = str(row.get('eventVenueName', 'Location TBD')).strip() or 'Location TBD'
        event_city = str(row.get('eventCity', '')).strip()
        event_state = str(row.get('eventState', '')).strip()

        venue_full = venue_name
        if event_city or event_state:
            venue_full += f" ({event_city}, {event_state})"

        description = str(row.get('event_description', 'No description available')).strip()
        if len(description) > 500:
            description = description[:500].rsplit(' ', 1)[0] + '...'
        description = description.replace('\n', '\n>')

        event_string += f"### 🎉 **[{event_name}]({event_url})**\n\n"
        event_string += f"👥 *Organization:* **{group_name}**\n\n"
        event_string += f"🕒 *When:* **{formatted_date}**\n\n"
        event_string += f"📍 *Where:* **{venue_full}**\n\n"
        event_string += f"📝 *Details:*\n> {description}\n\n"

    # Save Markdown
    with open(f'{name}.md', 'w', encoding='utf-8') as f:
        f.write(event_string)

    # Convert to HTML
    html_output = markdown.markdown(event_string, extensions=['extra', 'nl2br'])

    # Save HTML
    with open(f'{name}.html', 'w', encoding='utf-8') as f:
        f.write(html_output)



events_df = get_gsheet_df("Events")
create_event_markdown(events_df, "Chicago Events")



import pandas as pd
from dateutil import parser

def create_discord_list(event_df, name='Events'):
    # Safely parse dates
    def safe_parse_date(x):
        if pd.isnull(x) or str(x).strip() == "":
            return pd.NaT
        try:
            return parser.parse(str(x))
        except (parser.ParserError, ValueError, TypeError):
            return pd.NaT

    event_df = event_df.copy()

    # Safely clean up the eventStartTime column
    event_df['eventStartTime'] = event_df['eventStartTime'].apply(safe_parse_date)

    # Sort the events by date
    event_df = event_df.sort_values(by='eventStartTime', ascending=True)
    
    # Filter events before today
    now = pd.Timestamp.now()
    event_df = event_df[event_df['eventStartTime'].isna() | (event_df['eventStartTime'] >= now)]

    # Format the dates safely
    event_df['formatted_date'] = event_df['eventStartTime'].apply(
        lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else 'Date TBD'
    )

    # Deduplication
    event_df = event_df.drop_duplicates(subset='eventName', keep='first')
    event_df = event_df.drop_duplicates(subset=['eventStartTime', 'eventVenueName'], keep='first')

    event_string_len = 0
    event_string = ''

    # Build the event string
    for index, row in event_df.iterrows():
        event_name = str(row.get('eventName', 'Unnamed Event')).strip() or 'Unnamed Event'
        event_url = str(row.get('eventURL', '#')).strip() or '#'
        formatted_date = row.get('formatted_date', 'Date TBD') or 'Date TBD'

        event_string_to_add = f"* [{event_name}]({event_url}) - {formatted_date}\n"

        if event_string_len + len(event_string_to_add) > 2000:
            # Add two new lines to separate blocks
            event_string += '\n\n'
            event_string_len = 0

        event_string_len += len(event_string_to_add)
        event_string += event_string_to_add

    # Save to a file
    with open(f'{name} Discord List.txt', 'w', encoding='utf-8') as f:
        f.write(event_string)




events_df = get_gsheet_df("Events")
create_discord_list(events_df, "Chicago Events")



import pandas as pd
from datetime import datetime

def format_discord_event_posts(df: pd.DataFrame, max_chars: int = 1900) -> list:
    """
    Format DataFrame events into Discord-ready posts, minimizing character use to reduce total post count.
    """
    discord_posts = []
    current_post = []
    current_length = 0
    
    # Ensure required columns exist
    required_columns = ['eventName', 'eventStartTime', 'eventVenueName', 'groupName']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Sort by event time
    df = df.sort_values('eventStartTime')
    
    for _, row in df.iterrows():
        # Gather event details compactly
        event_name = row['eventName'] if pd.notna(row['eventName']) else "Event"
        org = row['groupName'] if pd.notna(row['groupName']) else "N/A"
        start_time = format_datetime(row['eventStartTime']) if pd.notna(row['eventStartTime']) else "N/A"
        venue = row['eventVenueName'] if pd.notna(row['eventVenueName']) else "N/A"
        event_url = row['eventURL'] if 'eventURL' in df.columns and pd.notna(row['eventURL']) else ""
        
        # One-liner event summary (condensed)
        event_line = f"- {event_name} | {start_time} | {org} | {venue}"
        if event_url:
            event_line += f" | {event_url}"

        # Add newline character
        event_line += "\n"
        
        # Check if adding this line exceeds the limit
        if current_length + len(event_line) > max_chars:
            discord_posts.append("".join(current_post))
            current_post = [event_line]
            current_length = len(event_line)
        else:
            current_post.append(event_line)
            current_length += len(event_line)
    
    if current_post:
        discord_posts.append("".join(current_post))
    
    return discord_posts

def format_datetime(dt) -> str:
    """Compact datetime format for brevity"""
    if isinstance(dt, str):
        try:
            dt = pd.to_datetime(dt)
        except:
            return dt
    if isinstance(dt, pd.Timestamp):
        return dt.strftime('%b %d %I:%M%p')  # e.g., "Apr 12 05:30PM"
    return str(dt)

def save_posts_to_file(posts: list, filename: str = "discord_posts.txt"):
    """Save formatted posts to a text file"""
    with open(filename, 'w', encoding='utf-8') as f:
        for i, post in enumerate(posts, 1):
            f.write(f"=== POST {i} ===\n")
            f.write(post)
            f.write("\n")
    print(f"Saved {len(posts)} posts to {filename}")

# Example usage
if __name__ == "__main__":
    # Example: combined_df = pd.read_csv("events.csv")
    posts = format_discord_event_posts(combined_df)
    save_posts_to_file(posts)


import re
import json
from datetime import datetime

def md_to_slack_blocks(md_content):
    MAX_BLOCKS_PER_MESSAGE = 50
    all_chunks = []
    current_blocks = []
    event_counter = 0

    def flush_blocks():
        if current_blocks:
            all_chunks.append({"blocks": list(current_blocks)})
            current_blocks.clear()

    # Precompile regex for efficiency
    event_splitter = re.compile(r'### 🎉 ')
    title_re = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    org_re = re.compile(r'\*Organization:\*\* ([^\n]+)')
    when_re = re.compile(r'\*When:\*\* ([^\n]+)')
    where_re = re.compile(r'\*Where:\*\* ([^\n]+)')
    details_re = re.compile(r'\*Details:\*\s*>([\s\S]+)')  # match multi-line details

    # Split events by header marker
    events = event_splitter.split(md_content)
    events = [e for e in events if e.strip()]  # Remove empty pieces

    # Create a Slack header
    header = {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "Upcoming Tech Events in Chicago",
            "emoji": True
        }
    }
    divider = {"type": "divider"}
    current_blocks.extend([header, divider])

    for event in events:
        event_counter += 1
        try:
            # Default safe placeholders
            title = "Unknown Title"
            url = "https://example.com"  # fallback URL
            org_text = "No Organization"
            when_text = "Date not specified"
            where_text = "Location not specified"
            details_text = "No details provided."

            # Try extracting fields individually
            title_match = title_re.search(event)
            if title_match:
                title, url = title_match.groups()

            org_match = org_re.search(event)
            if org_match:
                org_text = org_match.group(1).strip()

            when_match = when_re.search(event)
            if when_match:
                when_raw = when_match.group(1).strip()
                try:
                    dt = datetime.strptime(when_raw, "%A, %B %d @ %I:%M%p")
                    when_text = dt.strftime("%a %b %d at %I:%M %p")
                except ValueError:
                    when_text = when_raw  # Just use raw if parsing fails

            where_match = where_re.search(event)
            if where_match:
                where_text = where_match.group(1).strip()

            details_match = details_re.search(event)
            if details_match:
                details_text = details_match.group(1).strip().replace('\n', ' ')

            # Create Slack block
            event_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{url}|{title}>*\n:office: *Org:* {org_text}\n:calendar: *When:* {when_text}\n:round_pushpin: *Where:* {where_text}\n\n> {details_text[:200]}{'...' if len(details_text) > 200 else ''}"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "RSVP",
                        "emoji": True
                    },
                    "value": f"event_{re.sub(r'[^a-z0-9_]', '', title.lower().replace(' ', '_'))}",
                    "url": url,
                    "action_id": "rsvp_button"
                }
            }

            if len(current_blocks) + 2 > MAX_BLOCKS_PER_MESSAGE:
                flush_blocks()
                current_blocks.extend([header, divider])

            current_blocks.append(event_block)
            current_blocks.append(divider)

        except Exception as e:
            print(f"[Error] Failed to fully process event #{event_counter}: {e}")
            continue

    # Add final button
    final_button = {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View All Events",
                    "emoji": True
                },
                "value": "view_all",
                "url": "https://example.com/events",
                "action_id": "view_all_button"
            }
        ]
    }

    if len(current_blocks) + 1 > MAX_BLOCKS_PER_MESSAGE:
        flush_blocks()
        current_blocks.extend([header, divider])

    current_blocks.append(final_button)
    flush_blocks()

    print(f"[Success] Processed {event_counter} events into {len(all_chunks)} Slack message(s).")
    return all_chunks

# Example usage
if __name__ == "__main__":
    try:
        with open('Chicago Events.md', 'r', encoding='utf-8') as f:
            md_content = f.read()

        slack_blocks_chunks = md_to_slack_blocks(md_content)

        for i, chunk in enumerate(slack_blocks_chunks):
            print(f"\n--- Slack Message {i+1} ---\n")
            print(json.dumps(chunk, indent=2))

    except FileNotFoundError:
        print("[Error] 'Chicago Events.md' file not found.")
    except Exception as e:
        print(f"[Error] An error occurred: {e}")







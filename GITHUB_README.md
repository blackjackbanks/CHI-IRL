# CHI-IRL Event Scraper and Google Calendar Sync

## Project Overview
A Python-based event scraping and Google Calendar synchronization tool designed for CHI-IRL.

### Features
- Scrape events from multiple sources (Meetup, mHUB)
- Automatically add events to Google Calendar
- Web API for event submission
- Vercel deployment ready

### Prerequisites
- Python 3.9+
- Google Cloud Project
- Google Calendar API credentials

### Installation
1. Clone the repository
2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies
   ```bash
   pip install -r requirements-vercel.txt
   ```

### Configuration
1. Create a Google Cloud Project
2. Enable Google Calendar API
3. Download OAuth 2.0 credentials
4. Set environment variables:
   - `GOOGLE_CREDENTIALS`: Base64 encoded credentials
   - `CALENDAR_ID`: Primary Google Calendar ID

### Deployment
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

### Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### License
[Specify your license here]

### Contact
CHI-IRL Team
support@chi-irl.com

# CHI-IRL Event Scraper and Google Calendar Sync

## Project Overview
A Python-based event scraping and Google Calendar synchronization tool designed for CHI-IRL, enabling easy event discovery and calendar integration.

### Key Features
- 🌐 Web event scraping from multiple sources
- 📅 Automatic Google Calendar event synchronization
- 🔗 Flexible URL-based event submission
- 🚀 Vercel deployment ready

## Setup Instructions

### Prerequisites
- Python 3.9+
- Google Cloud Project
- Google Calendar API credentials

### 1. Create Google Cloud Project
- Go to the [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project
- Enable the Google Calendar API
- Create OAuth 2.0 credentials (Desktop app)
- Download the credentials JSON file

### 2. Install Dependencies
```bash
pip install -r requirements-vercel.txt
```

### 3. Prepare Credentials
Set environment variables:
- `GOOGLE_CREDENTIALS`: Base64 encoded credentials
- `CALENDAR_ID`: Primary Google Calendar ID

## Event Sources
Currently supports:
- Meetup.com events
- mHUB Chicago events

## Deployment Options

### Vercel Deployment
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

#### Deployment Steps
1. Install Vercel CLI
```bash
npm install -g vercel
vercel login
vercel
```

2. Set Environment Variables in Vercel Dashboard
- `GOOGLE_CREDENTIALS`
- `CALENDAR_ID`

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-vercel.txt

# Run the application
python app.py
```

## Carrd Website Integration

### Frontend JavaScript
```javascript
document.getElementById('event-form').addEventListener('submit', function(e) {
  e.preventDefault();
  const eventUrl = document.getElementById('event-url').value;
  
  fetch('https://your-vercel-app.vercel.app/add_event', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ event_url: eventUrl })
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success') {
      alert('Event added to calendar!');
    } else {
      alert('Error adding event');
    }
  });
});
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Troubleshooting
- Verify Python runtime compatibility
- Check Vercel/deployment logs
- Ensure all dependencies are in `requirements-vercel.txt`

## Security Considerations
- Use HTTPS for all API calls
- Implement rate limiting
- Validate and sanitize event URLs
- Use environment variables for sensitive credentials

## License
[Specify your license here]

## Contact
CHI-IRL Team
support@chi-irl.com

## Google Calendar Integration

### Setup Instructions

1. **Create Google Cloud Project**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download the credentials JSON file

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare CSV**
   Use `events_template.csv` as a guide. Ensure your CSV has these columns:
   - `summary`: Event title
   - `description`: Event details
   - `start_time`: Start time (ISO 8601 format)
   - `end_time`: End time (ISO 8601 format)

4. **Run the Integration**
   ```bash
   python google_calendar_sync.py
   ```
   - First run will open a browser for Google OAuth consent
   - Subsequent runs will use cached credentials

### Notes
- Times are in UTC by default
- Modify `timeZone` in code to change timezone
- Credentials are stored securely in `token.json`

## Event URL Integration

### Website Integration Methods

1. **Direct API Call**
   You can integrate the event URL submission into your existing website using two primary methods:

   a) **Backend Integration**
   ```python
   from event_scraper import EventScraper
   from google_calendar_sync import get_calendar_service

   def add_event_to_calendar(event_url):
       scraper = EventScraper()
       service = get_calendar_service()
       return scraper.process_and_add_event(event_url, service)
   ```

   b) **Frontend Form Submission**
   Create a form on your website that sends the event URL to your backend:
   ```html
   <form id="event-submission-form">
     <input type="url" id="event-url" placeholder="Paste event URL" required>
     <button type="submit">Add to Calendar</button>
   </form>
   ```

2. **Supported Event Sources**
   - Meetup.com events
   - mHUB Chicago events
   - More sources can be easily added by extending the `get_event_details` method

### Troubleshooting
- Ensure you have valid Google OAuth credentials
- Check network connectivity
- Verify event URL is from a supported source

### Security Considerations
- Implement URL validation
- Add rate limiting
- Use HTTPS for all communications

## Cloud Deployment

### Deployment Options
1. **PythonAnywhere**
   - Upload project files
   - Create a new web app
   - Set up virtual environment
   - Configure WSGI file to point to `app.py`

2. **Heroku**
   ```bash
   heroku create your-app-name
   heroku config:set GOOGLE_CREDENTIALS=$(cat credentials.json)
   git push heroku main
   ```

3. **Google Cloud Run**
   ```bash
   gcloud run deploy event-scraper \
     --source . \
     --allow-unauthenticated
   ```

4. **Vercel Deployment**

### Prerequisites
- Vercel CLI installed (`npm i -g vercel`)
- GitHub account
- Project repository on GitHub

### Deployment Steps
1. **Prepare Project**
   ```bash
   # Install Vercel CLI
   npm install -g vercel

   # Login to Vercel
   vercel login

   # Initialize project
   vercel
   ```

2. **Environment Variables**
   Set these in Vercel Dashboard:
   - `GOOGLE_CREDENTIALS`: Base64 encoded Google OAuth credentials
   - `CALENDAR_ID`: Primary Google Calendar ID

3. **Configuration Files**
   - `vercel.json`: Defines build and routing
   - `requirements-vercel.txt`: Specifies Python dependencies

### Carrd Integration Script
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

### Troubleshooting
- Verify Python runtime compatibility
- Check Vercel logs for deployment errors
- Ensure all dependencies are in `requirements-vercel.txt`

### Frontend Integration with Carrd
1. Add a custom HTML form to your Carrd site
2. Use JavaScript to submit event URL:
   ```javascript
   document.getElementById('event-form').addEventListener('submit', function(e) {
     e.preventDefault();
     const eventUrl = document.getElementById('event-url').value;
     
     fetch('https://your-deployed-app.com/add_event', {
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

### Security Considerations
- Use HTTPS for all API calls
- Implement rate limiting
- Validate and sanitize event URLs
- Use environment variables for sensitive credentials

## Notes
- Ensure you have the necessary Google Cloud permissions
- The app creates a BigQuery table automatically if it doesn't exist
- Each insertion generates a unique row ID

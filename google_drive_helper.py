import os
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
import mimetypes

class GoogleDriveHelper:
    def __init__(self, credentials_path):
        self.credentials_path = credentials_path
        self.service = self._get_drive_service()
        self.folder_id = None

    def _get_drive_service(self):
        """Initialize Google Drive service"""
        SCOPES = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        return build('drive', 'v3', credentials=creds)

    def create_events_folder(self):
        """Create or get the folder for event images"""
        folder_name = 'Event Images'
        
        # Search for existing folder
        results = self.service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        existing_folders = results.get('files', [])
        
        if existing_folders:
            self.folder_id = existing_folders[0]['id']
            print(f"Using existing folder: {folder_name}")
        else:
            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            self.folder_id = folder.get('id')
            print(f"Created new folder: {folder_name}")
        
        return self.folder_id

    def upload_image_from_url(self, image_url, event_name):
        """Download image from URL and upload to Google Drive"""
        try:
            # Ensure we have a folder
            if not self.folder_id:
                self.create_events_folder()

            # Download image
            response = requests.get(image_url)
            response.raise_for_status()
            
            # Determine file extension and mime type
            content_type = response.headers.get('content-type', 'image/jpeg')
            ext = mimetypes.guess_extension(content_type) or '.jpg'
            
            # Create file metadata
            file_metadata = {
                'name': f"{event_name}{ext}",
                'parents': [self.folder_id]
            }
            
            # Create media
            fh = BytesIO(response.content)
            media = MediaIoBaseUpload(
                fh,
                mimetype=content_type,
                resumable=True
            )
            
            # Upload file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            print(f"Uploaded image for event: {event_name}")
            return file.get('id'), file.get('webViewLink')
            
        except Exception as e:
            print(f"Error uploading image for {event_name}: {str(e)}")
            return None, None

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

            # Download image with timeout and proper error handling
            try:
                response = requests.get(image_url, timeout=15, stream=True)
                response.raise_for_status()
                
                # Check if the content is too large (>5MB)
                content_length = int(response.headers.get('content-length', 0))
                if content_length > 5 * 1024 * 1024:  # 5MB
                    print(f"Image too large ({content_length/1024/1024:.2f}MB): {image_url}")
                    return None, None
                
                # Get content
                image_content = response.content
                
                # Verify this is actually an image
                content_type = response.headers.get('content-type', 'image/jpeg')
                if not content_type.startswith('image/'):
                    print(f"URL does not point to an image (content-type: {content_type}): {image_url}")
                    return None, None
                
            except requests.exceptions.RequestException as e:
                print(f"Error downloading image from {image_url}: {str(e)}")
                return None, None
            
            # Determine file extension and mime type
            content_type = response.headers.get('content-type', 'image/jpeg')
            ext = mimetypes.guess_extension(content_type) or '.jpg'
            
            # Sanitize event name for filename
            safe_event_name = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in event_name)
            safe_event_name = safe_event_name[:50]  # Limit filename length
            
            # Create file metadata
            file_metadata = {
                'name': f"{safe_event_name}{ext}",
                'parents': [self.folder_id]
            }
            
            # Create media
            fh = BytesIO(image_content)
            media = MediaIoBaseUpload(
                fh,
                mimetype=content_type,
                resumable=True
            )
            
            # Upload file with retry
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    file = self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id, webViewLink'
                    ).execute()
                    
                    print(f"Uploaded image for event: {event_name}")
                    
                    # Make sure the file is accessible
                    self.service.permissions().create(
                        fileId=file.get('id'),
                        body={'type': 'anyone', 'role': 'reader'},
                        fields='id'
                    ).execute()
                    
                    return file.get('id'), file.get('webViewLink')
                except Exception as upload_error:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"Failed to upload after {max_retries} attempts: {str(upload_error)}")
                        return None, None
                    
                    print(f"Upload attempt {retry_count} failed: {str(upload_error)}. Retrying...")
                    import time
                    time.sleep(2 ** retry_count)  # Exponential backoff
            
            return None, None
            
        except Exception as e:
            print(f"Error uploading image for {event_name}: {str(e)}")
            return None, None

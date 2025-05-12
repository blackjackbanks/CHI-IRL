import base64

def encode_credentials(input_file='credentials.json', output_file='base64_credentials.txt'):
    """
    Encode Google OAuth credentials to base64
    
    Args:
        input_file (str): Path to the input credentials.json
        output_file (str): Path to save the base64 encoded credentials
    """
    try:
        # Read the credentials file
        with open(input_file, 'rb') as file:
            credentials = file.read()
        
        # Encode to base64
        base64_credentials = base64.b64encode(credentials).decode('utf-8')
        
        # Save to output file
        with open(output_file, 'w') as file:
            file.write(base64_credentials)
        
        # Print to console
        print("Base64 Encoded Credentials:")
        print(base64_credentials)
        print(f"\nCredentials saved to {output_file}")
        
        # Copy to clipboard if possible
        try:
            import pyperclip
            pyperclip.copy(base64_credentials)
            print("Credentials also copied to clipboard!")
        except ImportError:
            print("Install 'pyperclip' to automatically copy to clipboard")
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    encode_credentials()

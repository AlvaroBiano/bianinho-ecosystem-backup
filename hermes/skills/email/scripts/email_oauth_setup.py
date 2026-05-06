#!/usr/bin/env python3
"""
Email OAuth2 Setup for bianinhoclaw@gmail.com
Guides through Google OAuth2 configuration
"""
import os
import json
import subprocess
import sys

EMAIL = 'bianinhoclaw@gmail.com'
CREDENTIALS_FILE = os.path.expanduser('~/.hermes/email_credentials.json')
TOKEN_FILE = os.path.expanduser('~/.hermes/email_token.json')
CREDS_ENCRYPTED = os.path.expanduser('~/.hermes/email_creds.enc')

def check_gpg_key():
    """Check if GPG key exists for encryption"""
    result = subprocess.run(['gpg', '--list-secret-keys', EMAIL], 
                          capture_output=True, text=True)
    return result.returncode == 0

def store_app_password(app_password):
    """Store app password securely with GPG"""
    data = json.dumps({'email': EMAIL, 'app_password': app_password})
    
    # Encrypt to file
    with open(CREDS_ENCRYPTED, 'w') as f:
        subprocess.run(['gpg', '--encrypt', '--recipient', EMAIL],
                      input=data, text=True, stdout=f)
    
    print(f"✓ App password stored securely in {CREDS_ENCRYPTED}")

def setup_oauth():
    """Setup OAuth2 authentication"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     OAuth2 Setup for bianinhoclaw@gmail.com                ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    print("To set up OAuth2, you need to:")
    print("1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Click 'Create Credentials' → 'OAuth client ID'")
    print("3. Application type: 'Desktop app'")
    print("4. Name it: 'Hermes Email Agent'")
    print("5. Click 'Create'")
    print("6. Download the JSON file")
    print("7. Save it as: ~/.hermes/email_credentials.json")
    print("")
    print("Once done, run this script again to complete the setup.")
    print("")
    
    # Check if credentials file exists
    if os.path.exists(CREDENTIALS_FILE):
        print("✓ Credentials file found!")
        print("Completing OAuth2 authorization...")
        
        # Run OAuth flow
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.oauth2.credentials import Credentials
            
            SCOPES = [
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.modify'
            ]
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0, prompt='consent')
            
            # Save token
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
            
            print("✓ OAuth2 setup complete!")
            print(f"✓ Token saved to {TOKEN_FILE}")
            return True
            
        except Exception as e:
            print(f"ERROR during OAuth: {e}")
            return False
    else:
        print(f"⚠ Credentials file not found at {CREDENTIALS_FILE}")
        return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--app-password':
        # Store app password
        if len(sys.argv) > 2:
            store_app_password(sys.argv[2])
        else:
            print("Usage: python3 email_oauth_setup.py --app-password <password>")
    else:
        # Run OAuth setup
        setup_oauth()

if __name__ == '__main__':
    main()

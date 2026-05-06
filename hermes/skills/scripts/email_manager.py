#!/usr/bin/env python3
"""
Email Manager for bianinhoclaw@gmail.com
Uses Gmail OAuth2 for autonomous email access
"""
import os
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Config
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]
TOKEN_FILE = os.path.expanduser('~/.hermes/email_token.json')
CREDENTIALS_FILE = os.path.expanduser('~/.hermes/email_credentials.json')

def get_credentials():
    """Get valid OAuth2 credentials"""
    creds = None
    
    # Load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(creds)
    
    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if os.path.exists(CREDENTIALS_FILE):
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            save_credentials(creds)
        else:
            raise Exception("Credentials file not found. Please set up OAuth first.")
    
    return creds

def save_credentials(creds):
    """Save credentials to file"""
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())

def send_email(to_email, subject, body, html=False):
    """Send an email"""
    creds = get_credentials()
    
    message = MIMEMultipart('alternative' if html else 'mixed')
    message['to'] = to_email
    message['from'] = 'bianinhoclaw@gmail.com'
    message['subject'] = subject
    
    if html:
        message.attach(MIMEText(body, 'html'))
    else:
        message.attach(MIMEText(body, 'plain'))
    
    # Encode and send
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service = build_service(creds)
    
    return service.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()

def list_emails(max_results=10):
    """List recent emails"""
    creds = get_credentials()
    service = build_service(creds)
    
    results = service.users().messages().list(
        userId='me',
        maxResults=max_results,
        q='in:inbox is:unread'
    ).execute()
    
    messages = results.get('messages', [])
    return messages

def read_email(msg_id):
    """Read a specific email"""
    creds = get_credentials()
    service = build_service(creds)
    
    message = service.users().messages().get(
        userId='me',
        id=msg_id,
        format='full'
    ).execute()
    
    return message

def build_service(creds):
    """Build Gmail API service"""
    from googleapiclient.discovery import build
    return build('gmail', 'v1', credentials=creds)

if __name__ == '__main__':
    print("Email Manager for bianinhoclaw@gmail.com")
    print("Available commands: send, list, read")

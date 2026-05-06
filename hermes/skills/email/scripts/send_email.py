#!/usr/bin/env python3
"""
Email Sender for bianinhoclaw@gmail.com
Supports both App Password and OAuth2 authentication
"""
import os
import sys
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Config
EMAIL = 'bianinhoclaw@gmail.com'
CREDENTIALS_FILE = os.path.expanduser('~/.hermes/email_creds.enc')
OAUTH_TOKEN_FILE = os.path.expanduser('~/.hermes/email_token.json')

def load_credentials():
    """Load credentials from encrypted file or OAuth token"""
    import json
    import subprocess

    # Try GPG-encrypted app password first (current active setup)
    if os.path.exists(CREDENTIALS_FILE):
        try:
            result = subprocess.run(
                ['gpg', '--decrypt', CREDENTIALS_FILE],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get('app_password'), 'app_password'
        except:
            pass

    # Fallback: OAuth token (not yet fully configured)
    if os.path.exists(OAUTH_TOKEN_FILE):
        return None, 'oauth'

    return None, None

def send_email_smtp(to_email, subject, body, is_html=False):
    """Send email via SMTP"""
    creds, auth_type = load_credentials()

    if auth_type == 'oauth':
        # TODO: Implement OAuth2 SMTP
        print("OAuth2 not yet configured. Please set up App Password first.")
        return False

    if not creds:
        print("ERROR: No credentials found. Please configure email access.")
        print("Run: python3 ~/.hermes/skills/email/scripts/email_oauth_setup.py")
        return False
    
    msg = MIMEMultipart('html' if is_html else 'mixed')
    msg['From'] = EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL, creds)
            server.send_message(msg)
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"ERROR sending email: {e}")
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send email from bianinhoclaw@gmail.com')
    parser.add_argument('--to', required=True, help='Recipient email')
    parser.add_argument('--subject', required=True, help='Email subject')
    parser.add_argument('--body', required=True, help='Email body')
    parser.add_argument('--html', action='store_true', help='Send as HTML')
    
    args = parser.parse_args()
    success = send_email_smtp(args.to, args.subject, args.body, args.html)
    sys.exit(0 if success else 1)

import os
import base64
from email.mime.text import MIMEText
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    creds = None
    credentials_path = os.path.join('configs', 'credentials.json')
    print(credentials_path)

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_message(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except Exception as error:
        print('An error occurred: %s' % error)

def main():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    
    sender = "Lukas.zeppelin.ry@gmail.com"
    to = "Lukieminator@gmail.com"
    subject = "Test Email"
    message_text = "This is a test email from Python."
    
    message = create_message(sender, to, subject, message_text)
    send_message(service, 'me', message)

if __name__ == '__main__':
    main()

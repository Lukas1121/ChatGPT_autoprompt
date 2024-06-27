import os
import base64
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class EmailSender:
    def __init__(
        self, credentials_path="configs/credentials.json", token_path="token.json"
    ):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = self.authenticate_gmail()
        self.service = build("gmail", "v1", credentials=self.creds)

    def authenticate_gmail(self):
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
        return creds

    def create_message_with_attachment(self, sender, to, subject, message_text, files):
        message = MIMEMultipart()
        message["to"] = to
        message["from"] = sender
        message["subject"] = subject

        msg = MIMEText(message_text)
        message.attach(msg)

        for file in files:
            content_type, encoding = mimetypes.guess_type(file)
            if content_type is None or encoding is not None:
                content_type = "application/octet-stream"

            main_type, sub_type = content_type.split("/", 1)
            with open(file, "rb") as f:
                mime_base = MIMEBase(main_type, sub_type)
                mime_base.set_payload(f.read())
            encoders.encode_base64(mime_base)
            mime_base.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(file)}"',
            )
            message.attach(mime_base)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {"raw": raw_message}

    def send_message(self, sender, to, subject, message_text, files):
        message = self.create_message_with_attachment(
            sender, to, subject, message_text, files
        )
        try:
            sent_message = (
                self.service.users()
                .messages()
                .send(userId="me", body=message)
                .execute()
            )
            print("Message Id: %s" % sent_message["id"])
            return sent_message
        except Exception as error:
            print("An error occurred: %s" % error)
            return None

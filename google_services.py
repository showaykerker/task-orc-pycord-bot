"""
google_service.py
Wraps Google Forms and Google Drive APIs.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/forms','https://www.googleapis.com/auth/drive']

class GoogleService:
    """Google services integration base class."""

    def __init__(self, credentials_file):
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=SCOPES)
        self.forms_service = build('forms', 'v1', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)

    def create_form(self, title):
        """Creates a new form"""
        form = {'info': {'title': title}}
        created_form = self.forms_service.forms().create(body=form).execute()
        self.form_id = created_form["formId"]
        return created_form['formId']

    def add_questions(self):
        pass

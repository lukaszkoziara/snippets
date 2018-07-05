import logging

try:
    from apiclient.discovery import build
    from apiclient.errors import HttpError
    from google.oauth2 import service_account
except ImportError:
    logging.error('You should install Google Api Client lib: pip install google-api-python-client==1.7.3')

try:
    from oauth2client.file import Storage
except ImportError:
    logging.error('You should install oauth2client lib: pip install oauth2client==4.1.2')

from exceptions import WrongInitGAPIException


class GoogleDriveAPI:
    SCOPES = ['https://www.googleapis.com/auth/drive']

    def __init__(self, service_account_file=None, storage=None):
        if not service_account_file and not storage:
            raise WrongInitGAPIException('You should specify either service_account_file or storage file path')

        credentials = None
        if storage:
            storage = Storage(storage)
            credentials = storage.get()
        else:
            credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=self.SCOPES)

        if not credentials:
            raise WrongInitGAPIException('Unexpected credentials creation error')

        # cache_discovery=False due to googleapiclient cache import error
        # https://github.com/google/google-api-python-client/issues/299
        self.drive_handler = build('drive', 'v3', credentials=credentials, cache_discovery=False)
        self.current_mime_type = None

    @staticmethod
    def _query_from_dict(input_dict):
        return " and ".join(['{}=\'{}\''.format(key, value) for key, value in input_dict.items()])

    def file_media_handler(self, file_id):
        """File media handler

        Args:
            file_id (str): GDrive entry ID
        """
        return self.drive_handler.files().get_media(fileId=file_id)
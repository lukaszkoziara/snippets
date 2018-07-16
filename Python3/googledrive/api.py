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

from constants import DEFAULT_FIELDS, MimeType
from exceptions import EntryDoesNotExistGAPIException, MultipleObjectsReturnedGAPIException, \
    ArgumentNotFoundGAPIException, ResponseFormatGAPIException, WrongInitGAPIException
from queryset import GoogleDriveFolder, GoogleDriveFile
from result_helpers import GoogleDriveListIterator, GoogleDriveResult

logging.basicConfig(level=logging.WARNING)


class GoogleDriveAPI:
    """Google Drive API

    Args:
        service_account_file (str): path to GDrive credentials file

    Attributes:
        drive_handler (Resource): GDrive connection handler
        current_mime_type (MimeType): selected mime type

    Example:
        gapi = GoogleDriveAPI(service_account_file='/path/to/config/file')
        gapi = GoogleDriveAPI(storage='/path/to/store')
        gapi.get(id='123')
        gapi.get(name='test')
        gapi.folders.filter(name='test')
        gapi.folders.all()
    """

    SCOPES = ['https://www.googleapis.com/auth/drive']

    def __init__(self, service_account_file=None, storage=None):
        if not service_account_file and not storage:
            raise WrongInitGAPIException('You should specify either service_account_file or storage file path')

        credentials = None
        if storage:
            storage = Storage(storage)
            credentials = storage.get()
        else:
            credentials = service_account.Credentials.from_service_account_file(service_account_file,
                                                                                scopes=self.SCOPES)

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

    # ============================== gfile methods ==============================

    def get_gfile_meta_by_id(self, file_id, mime_type=None, selected_fields=''):
        """Google API call handler - get data by ID

        Args:
            file_id (str): ID of Google Drive entry/file/folder
            mime_type (str): MIME type of Google Drive entry/file/folder, eg. 'application/octet-stream'
            selected_fields (str): comma separated field names, which should be download with Google API response

        Returns:
             API response (GoogleDriveResult)

        Example:
            gapi_instance.get_gfile_meta_by_id('someTestId')
        """
        req_fields = selected_fields or DEFAULT_FIELDS

        if not file_id:
            raise ArgumentNotFoundGAPIException("You must pass 'file_id' parameter")

        if mime_type and 'mimeType' not in req_fields:
            raise ResponseFormatGAPIException(
                "You should set 'mimeType' field in fields declaration when using 'folders' filter method"
            )

        try:
            result = self.drive_handler.files().get(fileId=file_id, fields=req_fields).execute()
            if mime_type and result.get('mimeType') != mime_type:
                raise EntryDoesNotExistGAPIException(
                    "Mime type mismatch ('{}' != '{}')".format(mime_type, result.get('mimeType'))
                )
            return GoogleDriveResult(result, req_fields)
        except HttpError:
            raise EntryDoesNotExistGAPIException("Entry does net exist")

    def get_gfile_meta_by_name(self, name, mime_type=None, selected_fields=''):
        """
        Args:
            name (str): name of Google Drive entry/file/folder
            mime_type (str): MIME type of Google Drive entry/file/folder, eg. 'application/octet-stream'
            selected_fields (str): comma separated field names, which should be download with Google API response

        Returns:
             API response (GoogleDriveResult)

        Example:
            gapi_instance.get_gfile_meta_by_name('testName')
        """

        req_fields = selected_fields or DEFAULT_FIELDS

        if not name:
            raise ArgumentNotFoundGAPIException("You must pass 'file_name' parameter")

        # compose query dict
        query_dict = {'name': name}
        if mime_type:
            query_dict['mimeType'] = mime_type

        # api call
        result = self.drive_handler.files().list(
            q=self._query_from_dict(query_dict), fields='files({})'.format(req_fields)
        ).execute()
        files_result = result.get('files')

        if files_result:
            if len(files_result) > 1:
                raise MultipleObjectsReturnedGAPIException("Multiple object returned: {}".format(files_result))

            return GoogleDriveResult(files_result[0], req_fields)

        raise EntryDoesNotExistGAPIException("Empty result set")

    def get_gfiles_meta_by_name(self, name, mime_type=None, selected_fields=''):
        """
        Args:
            name (str): name of Google Drive entry/file/folder
            mime_type (str): MIME type of Google Drive entry/file/folder, eg. 'application/octet-stream'
            selected_fields (str): comma separated field names, which should be download with Google API response

        Returns:
             API response (GoogleDriveListIterator)

        Example:
            gapi_instance.get_gfiles_meta_by_name('testName')
        """
        req_fields = selected_fields or DEFAULT_FIELDS

        if not name:
            raise ArgumentNotFoundGAPIException("You must pass 'name' parameter")

        # compose query dict
        query_dict = {'name': name}
        if mime_type:
            query_dict['mimeType'] = mime_type

        params = {
            'q': self._query_from_dict(query_dict),
            'fields': 'files({}), nextPageToken'.format(req_fields)
        }

        # api call with result gather
        return GoogleDriveListIterator(self.drive_handler, params)

    def get_gfiles_meta(self, mime_type=None, selected_fields=''):
        """
        Args:
            mime_type (str): MIME type of Google Drive entry/file/folder, eg. 'application/octet-stream'
            selected_fields (str): comma separated field names, which should be download with Google API response

        Returns:
             API response (GoogleDriveListIterator)

        Example:
            gapi_instance.get_gfiles_meta()
        """
        req_fields = selected_fields or DEFAULT_FIELDS

        # compose query dict
        params = {
            'fields': 'files({}), nextPageToken'.format(req_fields)
        }

        if mime_type:
            params['q'] = self._query_from_dict({'mimeType': mime_type})

        return GoogleDriveListIterator(self.drive_handler, params)

    def get_gfiles_children_by_id(self, entry_id, mime_type=None, exclude_mime_type=None, selected_fields=''):
        """
        Args:
            entry_id (str): ID of Google Drive entry/file/folder
            mime_type (str): MIME type of Google Drive entry/file/folder, eg. 'application/octet-stream'
            exclude_mime_type (str): MIME type to exclude, eg. 'application/octet-stream'
            selected_fields (str): comma separated field names, which should be download with Google API response

        Returns:
             API response (GoogleDriveListIterator)

        Example:
            gapi_instance._get_gfiles_children_by_id('someId', mime_type=MimeType.GOOGLE_FOLDER_MIME_TYPE)
            gapi_instance._get_gfiles_children_by_id('someId', exclude_mime_type=MimeType.GOOGLE_FOLDER_MIME_TYPE)
        """

        req_fields = selected_fields or DEFAULT_FIELDS

        if not entry_id:
            raise ArgumentNotFoundGAPIException("You must pass 'entry_id' parameter")

        query = "'{}' in parents".format(entry_id)

        if mime_type:
            query = "{} and mimeType='{}'".format(query, mime_type)

        if exclude_mime_type:
            query = "{} and mimeType!='{}'".format(query, exclude_mime_type)

        params = {
            'q': query,
            'fields': 'files({}), nextPageToken'.format(req_fields)
        }

        return GoogleDriveListIterator(self.drive_handler, params)

    def create_gfile(self, name, mime_type=None, parents=None):
        """

        Args:
            name (str): name of Google Drive entry/file/folder
            mime_type (str): MIME type of Google Drive entry/file/folder, eg. 'application/octet-stream'
            parents (list): list of folder IDs

        Returns:
             pass

        Example:
            gapi_instance.create_gfile(
                'testName', mime_type=MimeType.GOOGLE_FOLDER_MIME_TYPE, parents=('testId',)
            )
        """
        file_metadata = {'name': name}

        if mime_type:
            file_metadata['mimeType'] = mime_type

        if parents:
            file_metadata['parents'] = parents

        return self.drive_handler.files().create(body=file_metadata, fields='id').execute().get('id')

    # ============================== api file methods ==============================

    @property
    def files(self):
        self.current_mime_type = None
        return GoogleDriveFile(self)

    # ============================== api folder methods ==============================

    @property
    def folders(self):
        self.current_mime_type = MimeType.GOOGLE_FOLDER_MIME_TYPE
        return GoogleDriveFolder(self)

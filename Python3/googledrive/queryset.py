import copy

from constants import DEFAULT_FIELDS, MimeType
from exceptions import MultipleObjectsReturnedGAPIException, ArgumentNotFoundGAPIException
from result_helpers import GoogleDriveFileDownloader, GoogleDriveFileUploader


class GoogleDriveEntry:
    """Google Drive Entry abstract class

    contains method to get or list data from Google API
    """

    def __init__(self, gapi_instance):
        self.gapi_instance = gapi_instance

    def get(self, entry_id=None, name=None, fields='', more_fields=''):
        """Basic get data method

        Args:
            entry_id (str): id of Google Drive`s entry/binary file/folder
            name (str): name of Google Drive`s entry/binary file/folder
            fields (str): comma separated field names, which should be download with Google API response
            more_fields (str): comma separated field names - additional field names to join to default fields

        Returns:
            Google API data (GoogleDriveResult)
        """

        func_name = None
        param_instance = None

        fields = fields or DEFAULT_FIELDS
        params = {
            'selected_fields': '{}, {}'.format(fields, more_fields) if more_fields else fields
        }

        if entry_id:
            func_name = 'get_gfile_meta_by_id'
            params['file_id'] = entry_id
        elif name:
            func_name = 'get_gfile_meta_by_name'
            params['name'] = name
        else:
            raise ArgumentNotFoundGAPIException("You must pass 'entry_id' or 'name' parameter")

        if self.gapi_instance.current_mime_type:
            mime_pass_through = copy.deepcopy(self.gapi_instance.current_mime_type)
            self.gapi_instance.current_mime_type = None
            params['mime_type'] = mime_pass_through

        return getattr(self.gapi_instance, func_name)(**params)

    def filter(self, name, fields='', more_fields=''):
        """Basic list elements with data method

        Args:
            name (str): name of Google Drive`s entry/binary file/folder
            fields (str): comma separated field names, which should be download with Google API response
            more_fields (str): comma separated field names - additional field names to join to default fields

        Returns:
            Google API data (list)
        """

        fields = fields or DEFAULT_FIELDS
        params = {
            'name': name,
            'selected_fields': '{}, {}'.format(fields, more_fields) if more_fields else fields
        }

        if self.gapi_instance.current_mime_type:
            mime_pass_through = copy.deepcopy(self.gapi_instance.current_mime_type)
            self.gapi_instance.current_mime_type = None
            params['mime_type'] = mime_pass_through

        return self.gapi_instance.get_gfiles_meta_by_name(**params)

    def all(self, fields='', more_fields=''):
        """Basic list of all elements

        Args:
            fields (str): comma separated field names, which should be download with Google API response
            more_fields (str): comma separated field names - additional field names to join to default fields

        Returns:
            Google API data (list)
        """

        fields = fields or DEFAULT_FIELDS
        params = {
            'selected_fields': '{}, {}'.format(fields, more_fields) if more_fields else fields
        }

        if self.gapi_instance.current_mime_type:
            mime_pass_through = copy.deepcopy(self.gapi_instance.current_mime_type)
            self.gapi_instance.current_mime_type = None
            params['mime_type'] = mime_pass_through

        return self.gapi_instance.get_gfiles_meta(**params)

    def exists(self, entry_id=None, name=None):
        """Basic exists data method

        Args:
            entry_id (str): id of Google Drive`s entry/binary file/folder
            name (str): name of Google Drive`s entry/binary file/folder

        Returns:
            info (bool)
        """

        try:
            result = self.get(entry_id=entry_id, name=name)
            if result and result.id is not None:
                return True
            return False
        except MultipleObjectsReturnedGAPIException:
            return True
        except Exception:
            return False


class GoogleDriveFile(GoogleDriveEntry):
    """Google Drive File abstract class

    contains method to get or list data from Google API
    """

    def upload_file(self, file_name, full_path, parent_folder_id=None):
        uploader = GoogleDriveFileUploader(file_name, full_path, parent_folder_id)
        return uploader.upload(self.gapi_instance.drive_handler)

    def get_downloader(self, file_id, file_handler=None):
        return GoogleDriveFileDownloader(
            self.gapi_instance.file_media_handler(file_id), file_handler=file_handler
        )


class GoogleDriveFolder(GoogleDriveEntry):
    """Google Drive Folder abstract class

    contains method to get or list data from Google API
    additional methods for folders-specific data: content (files inside folder), subfolders (folders inside folder)
    """

    def get_files(self, entry_id, fields='', more_fields=''):
        fields = fields or DEFAULT_FIELDS
        params = {
            'entry_id': entry_id,
            'exclude_mime_type': MimeType.GOOGLE_FOLDER_MIME_TYPE,
            'selected_fields': '{}, {}'.format(fields, more_fields) if more_fields else fields
        }

        return self.gapi_instance.get_gfiles_children_by_id(**params)

    def get_content(self, entry_id, fields='', more_fields=''):
        params = {
            'entry_id': entry_id,
            'selected_fields': '{}, {}'.format(fields, more_fields) if more_fields else fields
        }

        return self.gapi_instance.get_gfiles_children_by_id(**params)

    def get_subfolders(self, entry_id, fields='', more_fields=''):
        params = {
            'entry_id': entry_id,
            'mime_type': MimeType.GOOGLE_FOLDER_MIME_TYPE,
            'selected_fields': '{}, {}'.format(fields, more_fields) if more_fields else fields
        }

        return self.gapi_instance.get_gfiles_children_by_id(**params)

    def create(self, name, parents=None):
        return self.gapi_instance.create_gfile(
            name, mime_type=MimeType.GOOGLE_FOLDER_MIME_TYPE, parents=parents
        )

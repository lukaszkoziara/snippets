import io
import re

from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

from constants import DEFAULT_FIELDS, MimeType


class GoogleDriveResult:
    """Class for represent Google Drive query result instance

    Args:
        result_dict (dict): Google API response dict
        selected_fields (str): comma separated field names

    Info:
        contains properties extracted from API response dict
    """

    rename_attrs = {
        'mimeType': 'mime_type'
    }

    _default = ''
    _type = str
    _size_default = 0
    _size_type = int
    _parents_default = []
    _parents_type = list

    def __init__(self, result_dict, selected_fields=DEFAULT_FIELDS):
        for field in selected_fields.split(','):
            field = field.strip()

            default_value = getattr(self, '_{}_default'.format(field), self._default)
            default_type = getattr(self, '_{}_type'.format(field), self._type)

            new_field_name = self.rename_attrs.get(field, field)
            setattr(self, new_field_name, default_type(result_dict.get(field, default_value)))

    def __str__(self):
        return 'ID: {}'.format(getattr(self, 'id'))

    def __repr__(self):
        return '<ID: {} name: {} content type: {}>'.format(
            getattr(self, 'id'), getattr(self, 'name'), getattr(self, 'mime_type')
        )


class GoogleDriveListIterator:
    """API results iterator

    Args:
        drive_handler (build): Google API connection handler
        query_params (dict): connection params

    Returns:
        itself

    Info:
        pass

    Example:
        # init iterator:
        itit = GoogleDriveListIterator(drive_handler, params)

        # iterate over elements
        for elem in itit:
            pass

        # access arbitrary elem by index
        itit[0]

        # count elements
        itit.count()
        len(itit)
    """

    def __init__(self, drive_handler, query_params):
        # helper attributes
        self.token = None
        self._all_elements_cache = []
        self._all_data_completed = False

        # get arguments
        self.drive_handler = drive_handler
        self.base_query_params = query_params

        # extract fields info
        self.selected_fields = re.match('files\(([a-zA-Z,].*)\)', self.base_query_params.get('fields')).group(1)

    def _build_response_data(self, first_run=False):
        """ Handles consuming API date through requests

        Args:
            first_run (bool): whether call at init level or not
        """

        query_params = self.base_query_params
        query_params.pop('pageToken', None)  # clear page token

        # check token when iterate over pages
        if not first_run:
            if not self.token:
                return

            query_params['pageToken'] = self.token

        # call selected page
        resp = self.drive_handler.files().list(**query_params).execute()
        # prepare part of results
        self.list_to_consume = [GoogleDriveResult(elem, self.selected_fields) for elem in resp.get('files', [])]
        # update cache
        self._all_elements_cache.extend(self.list_to_consume)
        # catch new token
        self.token = resp.get('nextPageToken', None)

    def __getitem__(self, index):
        self._consume_iterator()
        return self._all_elements_cache[index]

    def __len__(self):
        """Handles elements count

        Returns:
            (int) elements count
        """

        self._consume_iterator()
        return len(self._all_elements_cache)

    def __iter__(self):
        """Handles iterator initialization

        Returns:
            itself
        """

        # reset iterator state
        if self._all_data_completed:
            return iter(self._all_elements_cache)

        self.token = None
        self._build_response_data(first_run=True)

        return self

    def __next__(self):
        """Handles next element extract

        Returns:
            (GoogleDriveResult) result object
        """

        if self.list_to_consume:
            return self._get_next_elem()
        else:
            self._build_response_data()

            if self.list_to_consume:
                return self._get_next_elem()
            else:
                self._all_data_completed = True
                raise StopIteration

    def _get_next_elem(self):
        return self.list_to_consume.pop(0)

    def _consume_iterator(self):
        """Handles simple iterator consumption
        """

        if not self._all_data_completed:
            for _ in self:
                pass

    def count(self):
        """Handles count elements

        Info:
            this is alternative for len() method; inspired by the Django queryset method
        """

        self._consume_iterator()
        return len(self._all_elements_cache)


class GoogleDriveFileDownloader:
    """GDrive file downloader

    Args:
        request - Google Api Client request to handle file download stream
        file_handler - any stream object handler, eg. BytesIO

    Example:
        gdownloader = GoogleDriveFileDownloader(self.gapi_instance.file_media_handler(file_id))
        gdownloader.download()
    """

    def __init__(self, request, file_handler=None):
        self.done = False
        self.file_handler = file_handler or io.BytesIO()
        self.downloader = MediaIoBaseDownload(self.file_handler, request)
        self.current_status = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.done:
            raise StopIteration
        else:
            current_status, self.done = self.downloader.next_chunk()
            return current_status

    def download(self, show_progress=False):
        """Download process evaluation

        Args:
             show_progress (bool): flag for enable progress printing

        Returns:
            None
        """
        if show_progress:
            # extract status info
            for current_status in self:
                print('Download {}%'.format(current_status.progress()))
        else:
            # just consume download process
            for elem in self:
                pass


class GoogleDriveFileUploader:

    def __init__(self, file_name, full_path, parent_folder_id=None):
        mime_type = MimeType.BINARY_MIME_TYPE
        # set metadata
        self.file_meta = {
            'name': file_name,
            'mimeType': mime_type
        }

        if parent_folder_id:
            self.file_meta['parents'] = [parent_folder_id]

        self.full_path = full_path
        self.mime_type = mime_type

    def upload(self, drive_handler):
        # init media data
        media = MediaFileUpload(self.full_path, mimetype=self.mime_type)

        # create file api call
        file = drive_handler.files().create(
            body=self.file_meta,
            media_body=media,
            fields='id'  # for return purpose
        ).execute()

        # close file in case of python warning
        # googledrive/api.py:279: ResourceWarning: unclosed file
        media._fd.close()

        return file.get('id')

# base fields list; by default Google API handles kind, id, name, mimeType fields
DEFAULT_FIELDS = 'kind, id, name, mimeType, size'


class MimeType:
    """Abstract class for holding mime types
    """

    DEFAULT_MIME_TYPE = 'application/octet-stream'
    BINARY_MIME_TYPE = 'application/octet-stream'
    GOOGLE_FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder'

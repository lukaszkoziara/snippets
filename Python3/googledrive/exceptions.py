class WrongInitGAPIException(Exception):
    """raises when initialization of GoogleDriveAPI failed
    """
    pass

class EntryDoesNotExistGAPIException(Exception):
    """raises when exact query returned empty set
    """
    pass


class MultipleObjectsReturnedGAPIException(Exception):
    """raises when exact query returned more then one record
    """
    pass


class ArgumentNotFoundGAPIException(Exception):
    """raises when too few parameters passed
    """
    pass


class ResponseFormatGAPIException(Exception):
    """raises when too few fields in query response declaration
    """
    pass

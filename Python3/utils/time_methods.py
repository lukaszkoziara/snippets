import datetime


DT_FILE_FORMAT = '%d_%m_%Y__%H_%M_%S'


def readable_time(seconds):
    """Returns human-readable time converted from seconds

    Args:
        seconds (float): result from time operation, eg. 12,67
    """
    hours = seconds // 3600
    seconds = seconds - (hours * 3600)

    minutes = seconds // 60
    seconds = seconds - (minutes * 60)

    return "{}h {}m {}s".format(int(hours), int(minutes), int(seconds))


def timestamped_filename(location, name, selected_time=None, file_type='errors'):
    """create filename with path and current date and time

    Args:
        location (str): path
        name (str): script specific name
        selected_time (str): custom datetime
        file_type (str): file suffix
    """
    if not selected_time:
        selected_time = datetime.datetime.now().strftime(DT_FILE_FORMAT)

    return os.path.join(location, '{}_{}_{}.txt'.format(file_type, name, selected_time))

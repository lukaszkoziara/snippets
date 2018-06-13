# python 2
import datetime
import os
import sys

from django.test.utils import override_settings


DT_FILE_FORMAT = '%d_%m_%Y__%H_%M_%S'


def cachalot_remover(func):
    """Cachalot remover decorator
    """
    def func_wrapper(*args, **kwargs):
        with override_settings(CACHALOT_ENABLED=False):
            func(*args, **kwargs)
    return func_wrapper


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


def timestamped_filename(location, name, selected_time=None):
    if not selected_time:
        selected_time = datetime.datetime.now().strftime(DT_FILE_FORMAT)

    return os.path.join(location, 'errors_{}_{}.txt'.format(name, selected_time))


class ProgressBar:
    """Progress bar class

    Args:
        all_count: number of all elements
    """

    def __init__(self, all_count):
        self.percent = 0
        self.all_count = float(all_count)

    def show_progress(self, progress_count):
        """prepare current progress status
        """
        result = int(progress_count / self.all_count * 100)
        if result >= self.percent:
            self.percent = result
            sys.stdout.write('\r{} {}%\r'.format('{}'.format('#' * self.percent).ljust(100, '-'), self.percent))

            if self.percent >= 100:
                sys.stdout.write('')  # go to newline

            sys.stdout.flush()

# python 2
import datetime
import glob
import os
import sys

from django.conf import settings
from django.test.utils import override_settings
import redis



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


def convert_size(size, precision=2):
    """Convert Bytes size to more readable format

    Args:
        size (int): number of Bytes, eg. 1231
        precision (int): precision size, eg. 2
    """
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    suffix_index = 0
    while size > 1024 and suffix_index < 4:
        suffix_index += 1  # increment the index of the suffix
        size = size / 1024.0  # apply the division
    return "%.*f%s" % (precision, size, suffixes[suffix_index])


def chunks_gen(elements, output_size=100):
    """Yield successive n-sized chunks from l.

    Args:
        elements (iter): iterable with many elements, eg. [1,2,3]
        output_size (int): batch size, eg. 100
    """
    for i in range(0, len(elements), output_size):
        yield elements[i:i + output_size]


def ask(question, default='y'):
    """Yes/No input getter

    Args:
        question (str): question, eg. 'Are You sure?'
        default (str): default answer, eg. 'y'

    Usage:
        if not ask('Continue?', 'n'):
            sys.exit()
    """
    resp = input(question + (' [Y/n] (default: %s)' % default)).lower()
    if resp not in ['y', 'n', '']:
        print 'what?'
        return ask(question)
    return resp == 'y' or (resp == '' and default == 'y')


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


class GlobFilesGenerator:
    """Implements iterate methods over files

    Args:
        location (str): path to disk location, eg. location='/home/test/'
        pattern (str): regex pattern, eg. pattern='*.bman'
        debug (bool): debug flag, eg. debug=True

    Usage:
        for elem in GlobFilesGenerator(some_location, pattern='*.jpg', debug=True):
            do_sth(elem)
    """

    default_pattern = ''
    default_start_message = 'Reading files from disk...'

    def __init__(self, location, pattern=None, debug=False, set_len=False, sort_key=None):
        """Set data and init glob generator"""
        print self.default_start_message

        self.debug = debug
        self.counter = 0
        self.pattern = pattern if pattern else self.default_pattern

        self.glob_gen = glob.iglob(os.path.join(location, self.pattern))  # standard glob generator

        self.all_files_count = 0
        if self.debug or set_len:
            # check number of files
            self.all_files_count = 0 if not self.debug else len(list(self.glob_gen))
            # load glob generator anyway to override list call
            self.glob_gen = glob.iglob(os.path.join(location, self.pattern))

    def __iter__(self):
        """Default iterator method"""
        return self

    def __next__(self):
        """Grab glob generator result element"""
        next_elem = self.glob_gen.__next__()
        # debug info
        if self.debug:
            self.counter += 1
            print '{}/{} - {}'.format(self.counter, self.all_files_count, next_elem)
        return next_elem


class RedisConn():
    """simple redis context manager

    Usage:
        with RedisConn() as fastcache:
            fastcache.get(key)
    """

    def __init__(self):
        self.r_conn = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                                           db=settings.TMP_REDIS_CACHE_DB)
        self.fastcache = redis.Redis(connection_pool=self.r_conn)

    def __enter__(self):
        return self.fastcache

    def __exit__(self, exc_type, exc_value, traceback):
        self.r_conn.disconnect()

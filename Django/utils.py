# python 3
import glob
import os

from django.conf import settings
from django.test.utils import override_settings
import redis


def cachalot_remover(func):
    """Cachalot remover decorator
    """
    def func_wrapper(*args, **kwargs):
        with override_settings(CACHALOT_ENABLED=False):
            func(*args, **kwargs)
    return func_wrapper


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

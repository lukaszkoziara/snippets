import inspect
import logging
import time

import redis

REDIS_CONN_RETRY_MAX = 3
REDIS_CONN_SLEEP_TIME = 5

logger = logging.getLogger(__name__)


def redis_deco_wrapper_class_decorator(cls):
    """Redis connection class all methods decorator

    Example:
        redis_conn_retry_deco(method)
        or
        @redis_conn_retry_deco()
        def some_method():
            pass
    """

    for name, method in inspect.getmembers(cls, inspect.isfunction):
        if '_' not in name:
            setattr(cls, name, redis_conn_retry_deco(method))
    return cls


def redis_conn_retry_deco(func):
    """Redis connection retry decorator

    Attributes:
        deco_tries (int): keep retries count
        sleep_time (int): time to sleep in seconds

    Example:
        @redis_conn_retry_deco
        class SomeClass(redis.Redis):
            pass
    """

    def wrapper(*args, **kwargs):
        deco_tries = 1
        last_err = None
        sleep_time = REDIS_CONN_SLEEP_TIME

        while deco_tries <= REDIS_CONN_RETRY_MAX:
            try:
                result = func(*args, **kwargs)
                return result
            except (redis.exceptions.ConnectionError, redis.exceptions.BusyLoadingError) as err:
                logger.warning('Redis connection timeout. Going to sleep for {}s and retrying ({}/{})'.format(
                    REDIS_CONN_SLEEP_TIME, deco_tries, REDIS_CONN_RETRY_MAX
                ))
                last_err = err
                time.sleep(sleep_time)
                deco_tries += 1
                sleep_time += 5
        raise last_err

    return wrapper


@redis_deco_wrapper_class_decorator
class RedisDecoWrapper(redis.Redis):
    """Redis wrapper

    Args:
        as in original redis.Redis class

    Note:
        main purpose of this class is decorate all Redis methods with retry connection wrapper
    """
    pass


class RedisConn:
    """Redis connection helper class

    Args:
        settings (dict): dict with DBs connection data
        db_key (str): DB name as key from REDIS_DATABASES dict

    Note:
        implemented as context manager

    Example:
        REDIS_DATABASES = {
            'default': {
                'host': '127.0.0.1',
                'port': 6379,
                'db': 0
            },
        }
        with RedisConn(REDIS_DATABASES) as fastcache:
            fastcache.something()
    """

    def __init__(self, settings_dict, db_key='default'):
        self.r_conn = redis.ConnectionPool(**settings_dict.get(db_key))
        self.fastcache = RedisDecoWrapper(connection_pool=self.r_conn)

    def __enter__(self):
        return self.fastcache

    def __exit__(self, exc_type, exc_value, traceback):
        self.r_conn.disconnect()

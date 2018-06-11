# python 2
from django.test.utils import override_settings


def cachalot_remover(func):
    """Cachalot remover decorator
    """
    def func_wrapper(*args, **kwargs):
        with override_settings(CACHALOT_ENABLED=False):
            func(*args, **kwargs)
    return func_wrapper

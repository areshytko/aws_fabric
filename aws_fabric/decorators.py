
from functools import wraps
import inspect
import time


def autodoc(func):
    """
    puts function signature inside its' docstring
    """

    argspec = inspect.getargspec(func)
    args = argspec.args
    defaults = argspec.defaults
    if defaults is None:
        defaults = []

    without_defaults = args[:len(args) - len(defaults)]
    with_defaults = ['%s=%s' % (k, v) for k, v in zip(args[len(args) - len(defaults):], defaults)]
    arg_string = ','.join(without_defaults + with_defaults)
    if arg_string:
        arg_string = ':' + arg_string

    if not func.__doc__:
        func.__doc__ = arg_string
    else:
        func.__doc__ = arg_string + '\n' + func.__doc__

    @wraps(func)
    def wrapped(*args, **kwargs):
        func(*args, **kwargs)

    return wrapped


def with_retry(delay_time, retry_count=None):
    def _with_retry(func):

        @wraps(func)
        def decorated(*args, **kw):
            count = 0
            while count < retry_count if retry_count else True:
                try:
                    result = func(*args, **kw)
                    return result
                except Exception as e:
                    print e
                    count += 1
                    time.sleep(delay_time)

        return decorated
    return _with_retry


def timing(func):

    @wraps(func)
    def wrap(*args, **kw):
        time1 = time.time()
        ret = func(*args, **kw)
        time2 = time.time()
        print '%s function took %0.3f ms' % (func.func_name, (time2-time1)*1000.0)
        return ret

    return wrap
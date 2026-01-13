from time import time

from uuid_extensions import uuid7


def get_time(seconds_precision=True):
    """Return current time as Unix/Epoch timestamp, in seconds.
    :param seconds_precision: if True, return with seconds precision as integer (default).
                              If False, return with millisecond precision as floating point number of seconds.
    """
    return time() if not seconds_precision else int(time())


def get_uuid():
    """Return a UUID7 as string"""
    return str(uuid7())

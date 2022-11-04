from functools import wraps
from time import time

import logger_helper

LOG = logger_helper.factory_logger()


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        LOG.debug('func:%r args:[%r, %r] took: %2.4f sec' % \
                  (f.__name__, args, kw, te - ts))
        return result

    return wrap


def log_in_out(f):
    @wraps(f)
    def wrap_log_in_out(*args, **kw):
        ts = time()
        LOG.debug("Entrando {}".format(f.__name__))
        result = f(*args, **kw)
        te = time()
        LOG.debug('Saindo: func:%r took: %2.4f sec  ' % (f.__name__, te - ts))
        return result

    return wrap_log_in_out

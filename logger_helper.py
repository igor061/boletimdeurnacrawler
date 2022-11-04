import logging
import inspect
import os.path

"""
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s() - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
LOG.addHandler(ch)
"""


def _extract_filename(full_filename):
    return os.path.splitext(os.path.basename(full_filename))[0]


def _get_caller_filename():
    return _extract_filename(inspect.stack()[2].filename)


def factory_logger():
    logger_name = _get_caller_filename()
    log = logging.getLogger(logger_name)
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s() - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    return log
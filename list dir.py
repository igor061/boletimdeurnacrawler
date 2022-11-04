from glob import glob
from time import sleep

from logger_helper import factory_logger

LOG = factory_logger()
last = 0
while True:
    leng = len(glob('C:\\bu\\**\\*.bu', recursive=True))
    LOG.debug(f"{leng-last}, {leng}")
    last = leng
    sleep(10)

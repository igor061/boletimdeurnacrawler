from collections import deque
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from pprint import pprint
from time import sleep

import logger_helper

LOG = logger_helper.factory_logger()

import queue

from requests import Session
from requests_futures.sessions import FuturesSession

from elapsed_time_decorator import log_in_out
import list_urls


def default_hook(resp, *args, **kwargs):
    resp.data = resp.content


def json_hook(resp, *args, **kwargs):
    resp.data = resp.json()


def future_get(session, hooks, url):
    future = session.get(url, hooks=hooks)
    future.url = url
    return future


@log_in_out
def execute_get_list_urls(lista, max_works=20, session=Session(),
                          response_hook=default_hook, ignore_result=False, executor=ThreadPoolExecutor):

    hooks = {'response': response_hook}
    with FuturesSession(executor=executor(max_workers=max_works), session=session) as session:
        futures = [future_get(session, hooks, url) for url in lista]


        print("foi tudo")
        fails = []
        if ignore_result:
            for future in futures:
                try:
                    future.result()

                except Exception as excpt:
                    pprint(excpt)
                    fails.append(future)

            resp = None
        else:
            resp = [future.result().data for future in futures]

    return resp, fails


if __name__ == '__main__':
    @log_in_out
    def teste01():
        LOG.debug("######## - teste01 - ############")
        lista_urls = list_urls.list_urls_df
        queue_1 = deque()
        results = execute_get_list_urls(lista_urls[:2])
        [queue_1.append(result) for result in results]
        pprint(queue_1)


    @log_in_out
    def teste02():
        qq_in = queue.Queue()
        lista_urls = list_urls.list_urls_df
        print(len(lista_urls))
        [qq_in.put(url) for url in lista_urls]
        LOG.debug(f"qq_in len {qq_in.qsize()}")


    teste01()

#   with FuturesSession(executor=ProcessPoolExecutor(max_workers=max_works), session=session) as session:


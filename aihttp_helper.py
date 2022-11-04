import traceback
from pprint import pprint
from collections.abc import Callable
from typing import List
import aiohttp
import asyncio


from elapsed_time_decorator import log_in_out


class AioHttpRequest:
    METH_POST = "POST"
    METH_GET = "GET"

    @staticmethod
    async def response_hook_json(response):
        #pprint(dir(response))
        response.raise_for_status()
        resp = await response.json(content_type=None)

        return resp

    @staticmethod
    async def response_hook_default(response):
        response.raise_for_status()
        resp = await response.read()
        return resp

    def __init__(self, url, method=METH_GET, response_hook: Callable = response_hook_default, **kwargs):
        self.url = url
        self.method = method
        self.kwargs = kwargs
        self.response_hook = response_hook
        self.result = None
        self.exception = None
        self.tracebak = None

    def __str__(self):
        return f"{self.url}"

    def __repr__(self):
        return self.__str__()

    async def do(self, session: aiohttp.ClientSession, **kwargs):
        try:
            async with session.request(self.method, self.url, **kwargs) as response:
                result = await self.response_hook(response)
                self.result = result
                return result
        except Exception as ex:
            self.exception = ex
            self.tracebak = traceback.format_exc()
            return ex

    def reset(self):
        self.result = None
        self.exception = None
        self.tracebak = None
        return self


class AioHttpHelper:

    def __init__(self, **kwargs):
        self._workers: int = kwargs.get('workers', 100)
        self._ttl_dns_cache: int = kwargs.get('ttl_dns_cache', 10)
        self._ssl_check: bool = kwargs.get('ssl_check', True)

    async def _get_page(self, session: aiohttp.ClientSession, request, **kwargs):
        return await request.do(session, **kwargs)

    @log_in_out
    def _creater_tasks(self, *args, **kwargs):
        session, urls = args

        tasks = []

        for url in urls:
            task = asyncio.create_task(self._get_page(session, url, **kwargs))
            tasks.append(task)

        return tasks

    async def _get_all(self, session: aiohttp.ClientSession, requests, **kwargs):
        tasks = self._creater_tasks(session, requests, **kwargs)

        results = await asyncio.gather(*tasks)

        return results

    async def get_urls_list(self, requests: List[AioHttpRequest], **kwargs):
        workers = kwargs.pop('max_works', self._workers)
        ttl_dns_cache = kwargs.get('ttl_dns_cache', self._ttl_dns_cache)
        ssl_check = kwargs.get('ssl_check', self._ssl_check)
        response_hook = kwargs.get('response_hook', )
        async with aiohttp.TCPConnector(
                limit=workers,
                ttl_dns_cache=ttl_dns_cache,
                ssl=ssl_check
        ) as conn:
#        puser = "cLgbgE3Rc:DWRFIJR1pKz"
#        pport = "1080"
#        list=[
#                f"socks5://{puser}@syd.socks.ipvanish.com:{pport}/",
#                f"socks5://{puser}@tor.socks.ipvanish.com:{pport}/",
#                f"socks5://{puser}@par.socks.ipvanish.com:{pport}/",
#                f"socks5://{puser}@fra.socks.ipvanish.com:{pport}/",

                #]
        #async with ProxyConnector.from_url(list[0], limit=20) as conn:
            async with aiohttp.ClientSession(connector=conn) as session:
                data = await self._get_all(session, requests, **kwargs)
                return data

    @log_in_out
    def work(self, urls: List[AioHttpRequest], **kwargs):
        results = asyncio.run(self.get_urls_list(urls, **kwargs))
        return results


if __name__ == '__main__':
    nn = 5

    # _urls = [AioHttpRequest('http://httpbin.org/delay/2')]*nn
    # _urls = [AioHttpRequest('http://httpbin.org/ip')]*nn
    # _urls = [AioHttpRequest('http://httpbin.org/anything/asdf', AioHttpRequest.METH_POST, data={'qwe': 'qwe'})] * nn
    # _urls = [AioHttpRequest('http://httpbin.org/drip?duration=2&numbytes=10&code=200&delay=2')]*nn
    # _urls = [AioHttpRequest('https://reqbin.com/sample/post/json', AioHttpRequest.METH_POST, data={'qwe': 'qwe'})] * 1
    #_urls = [AioHttpRequest('https://www.vestibularfatec.com.br/classificacao/lista.asp',
#                            AioHttpRequest.METH_POST, data={'CodFatec': 5}
#                            )] * 1

    _urls = [AioHttpRequest('http://httpbin.org/ip',
                            AioHttpRequest.METH_GET,
                            )] * 4

    "https://www.vestibularfatec.com.br/classificacao/lista.asp"
    aiht = AioHttpHelper(workers=nn)

    resp = aiht.work(_urls, )

    pprint([(i.result, i.exception) for i in _urls])

import requests
from requests_futures.sessions import FuturesSession

import logger_helper
from elapsed_time_decorator import log_in_out

log = logger_helper.factory_logger()


class ProgressStatus:
    def __init__(self):
        self._total, self._done = 0, 0

    def add(self, future):
        self._total += 1

    def done(self, future):
        self._done += 1

    def progress(self):
        return self._done, self._total

    def finished(self):
        return self._total == self._done

    def __iter__(self):
        while True:
            yield self.progress()

            if self.finished():
                yield self.progress()  # make sure we inform the final status
                raise StopIteration


class ProgressFuturesSession(FuturesSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.status = ProgressStatus()

    def request(self, *args, **kwargs):
        future = super().request(*args, **kwargs)
        future.add_done_callback(self.status.done)
        self.status.add(future)


def session_factory(cookie_string=None, max_workers=10, cache_dir=None, cache_days=7, cache_forever=False):
    session = requests.Session()

    if cookie_string:
        session.cookies = cookiejar_from_str(cookie_string)

    if cache_dir:
        log.debug('Using CacheControl: dir=%r, days=%r, forever=%r', cache_dir, cache_days, cache_forever)
        session = CacheControl(
            session,
            cache=FileCache(cache_dir, forever=cache_forever),
            heuristic=ExpiresAfter(days=cache_days)
        )

    return session


class HttpHelper:
    session = requests.Session()
    last_resp = None

    def __init__(self):
        pass

    def _session_init(self):
        return requests.Session()

    @log_in_out
    def do_post(self, url, data, cookies_add=None):

        if cookies_add:
            cookies = self.session.cookies.get_dict()
            if cookies_add:
                for chave, value in cookies_add.items():
                    cookies[chave] = value
            #print(cookies)
        else:
            cookies = self.session.cookies

        resp = self.session.post(url, data, cookies=cookies)
        #print(resp)
        self.last_resp = resp
        if 200 != resp.status_code:
            raise ConnectionError('Ao pegar a url [{}], code [{}]'.format(url, resp.status_code))
        return HttpHelper.byte_str(resp)

    @staticmethod
    def byte_str(response):
        return response.content.decode(response.encoding)
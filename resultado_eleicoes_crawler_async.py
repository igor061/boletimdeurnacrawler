import asyncio
import os
from glob import glob
from pprint import pprint
from string import Template
from time import sleep

import aiofiles
import aiohttp



from elapsed_time_decorator import log_in_out
from logger_helper import factory_logger
from aihttp_helper import AioHttpHelper, AioHttpRequest

LOG = factory_logger()


class FileHelper:
    @staticmethod
    def dump(arquivo, data):

        with open(arquivo, 'wb') as f:
            f.write(data)

        return arquivo

    @staticmethod
    def dump_create_dirs(arquivo, data):
        try:
            FileHelper.dump(arquivo, data)
        except FileNotFoundError:
            try:
                os.makedirs(os.path.dirname(arquivo))
            except FileExistsError:
                pass

            FileHelper.dump(arquivo, data)

    @staticmethod
    def load(arquivo):
        with open(arquivo, 'rb') as f:
            resp = f.read()

        return resp


set_files = set([f"{x[:-91]}*.bu".replace('\\', '/') for x in glob('C:\\bu\\**\\*.bu', recursive=True)])
print("set ok")


class BuFile:
    template_file_name = Template("${sigla_estado}-${id_municipio}-${zona_eleitoral}-${secao_eleitoral}-${bu_hash}.bu")
    template_path_dir = Template("${sigla_estado}/${id_municipio}/${zona_eleitoral}/")
    template_path = Template("${path_raiz}${path_dir}${file_name}")

    def __init__(self, urna, path_raiz='bu/'):
        self.urna = urna
        self.urna_dict = {
            'sigla_estado': urna.sigla_estado,
            'id_municipio': urna.id_municipio,
            'zona_eleitoral': urna.zona_eleitoral,
            'secao_eleitoral': urna.secao_eleitoral,
            'bu_hash': urna.bu_hash,

        }

        self.path_raiz = path_raiz

    def filename(self, any_hash=False):
        dct = self.urna_dict
        if any_hash:
            dct = dct.copy()
            dct['bu_hash'] = '*'

        return self.template_file_name.substitute(**dct)

    def path_dir(self):
        return self.template_path_dir.substitute(**self.urna_dict)

    def path(self, any_hash=False):
        return self.template_path.substitute(
            path_raiz=self.path_raiz, path_dir=self.path_dir(), file_name=self.filename(any_hash))

    def grava_arquivo(self, dados):
        file_path = self.path()

        FileHelper.dump_create_dirs(file_path, dados)
        return file_path

    def exist(self):
        return len(glob(self.path(any_hash=True))) > 0

    def pre_exist(self):
        return self.path(any_hash=True) in set_files


class Urna:
    url_root = "https://resultados.tse.jus.br/oficial/ele2022/"

    def __init__(self, id_pleito, sigla_estado, municipio, zona_eleitoral, secao_eleitoral):
        self.id_pleito = f"0000{id_pleito}"[-5:]
        self.sigla_estado = sigla_estado.lower()
        self.id_municipio = f"0000{municipio}"[-5:]
        self.zona_eleitoral = f"000{zona_eleitoral}"[-4:]
        self.secao_eleitoral = f"000{secao_eleitoral}"[-4:]
        self.url_root_dados_urna = self.create_url_root_dados_urna()
        self.url_json_dados_urna = self.create_url_json_dados_urna()
        self.template_url_bu = self.create_template_url_bu()
        self.bu_hash = None

    def __str__(self):
        return f"{self.sigla_estado}-{self.id_municipio}-{self.zona_eleitoral}-{self.secao_eleitoral}"

    def create_url_root_dados_urna(self):
        resp = f"{Urna.url_root}arquivo-urna/{int(self.id_pleito)}/dados/" \
               f"{self.sigla_estado}/{self.id_municipio}/{self.zona_eleitoral}/{self.secao_eleitoral}/"

        return resp

    def create_url_json_dados_urna(self):
        resp = f"{self.url_root_dados_urna}" \
               f"p0{self.id_pleito}-{self.sigla_estado}" \
               f"-m{self.id_municipio}-z{self.zona_eleitoral}-s{self.secao_eleitoral}-aux.json"

        return resp

    def create_template_url_bu(self):
        arq_bu = f"o{self.id_pleito}-{self.id_municipio}{self.zona_eleitoral}{self.secao_eleitoral}.bu"

        resp = Template(f"{self.url_root_dados_urna}$bu_hash/{arq_bu}")

        return resp

    def url_bu(self, bu_hash):
        file_path = BuFile(self).path()
        #resp = "http://192.168.15.3/"+file_path
        #print(resp)
        #return resp

        return self.template_url_bu.substitute(bu_hash=bu_hash)

    @staticmethod
    def get_hash_from_jsn_sessao(jsn):
        return jsn['hashes'][0]['hash']

    def set_bu_hash(self, jsn):
        bu_hash = Urna.get_hash_from_jsn_sessao(jsn)
        self.bu_hash = bu_hash
        return bu_hash

    def url_bu_from_json(self, jsn):
        bu_hash = self.set_bu_hash(jsn)
        self.bu_hash = bu_hash

        return self.url_bu(bu_hash)

    def get_json(self):
        resp = RequestHelper.get(
            self.url_json_dados_urna
        )

        return resp.json()

    def get_bu_json(self, jsn):
        url_bu = self.url_bu_from_json(jsn)
        arq = RequestHelper.get(url_bu)

        return arq.content

    def get_bu(self):
        jsn = self.get_json()
        bu = self.get_bu_json(jsn)
        return bu


class ResultadoEleicoesWorkers:

    def __init__(self, eleicao_id, base_url):
        pass


class ResultadoEleicoesCrawler:

    lista_estados = (
        'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 'ma',
        'mt', 'ms', 'mg', 'pr', 'pb', 'pa', 'pe', 'pi', 'rj', 'rn',
        'rs', 'ro', 'rr', 'sc', 'se', 'sp', 'to', 'zz',
    )

    def __init__(self, id_pleito, url_base, workers):
        self.id_pleito = f"0000{id_pleito}"[-5:]

        self.url_base = url_base
        self.template_url_base_lista_municipios = self._create_template_url_base_lista_municipios()

        self.aiohttp = AioHttpHelper()
        self.workers = workers

    def _create_template_url_base_lista_municipios(self):

        resp = Template(f"{self.url_base}arquivo-urna/{int(self.id_pleito)}/config/" \
                        f"$sigla_estado/$sigla_estado-p0{self.id_pleito}-cs.json")

        return resp

    def pega_json_municipios(self, sigla_estado):
        url = self.template_url_base_lista_municipios.substitute(sigla_estado=sigla_estado)
        # print(url)

        resp = RequestHelper.get(url)

        return resp.json()

    @staticmethod
    def generator_lista_sessoes_uf(json_municipios):
        js = json_municipios['abr'][0]

        sigla_estado = js['cd']

        for municipio in js['mu']:
            id_municipio = municipio['cd']
            for zn in municipio['zon']:
                zona = zn['cd']
                for secao in zn['sec']:
                    yield sigla_estado, id_municipio, zona, secao['ns']

    async def list_municipios_hook(self, resp, *args, **vargs):
        jsn = await AioHttpRequest.response_hook_json(resp)
        jsn = await AioHttpRequest.response_hook_json(resp)
        gen_sessao = self.generator_lista_sessoes_uf(jsn)
        return [sessao for sessao in gen_sessao]

    def load_list_sessoes_list_uf(self, list_uf):
        list_request_jsn_municipios = [
            AioHttpRequest(
                self.template_url_base_lista_municipios.substitute(sigla_estado=uf),
                response_hook=self.list_municipios_hook,
            ) for uf in list_uf
        ]

        list_uf_list_sessao = self.aiohttp.work(
            list_request_jsn_municipios,
            max_works=self.workers,

        )

        pprint("FAILS")
        for req in list_request_jsn_municipios:
            if req.exception:
                raise req.exception

        # pprint(list_json_municipios)
        return list_uf_list_sessao

    def generator_urna(self, list_uf_list_sessao):
        for list_sessao_uf in list_uf_list_sessao:
            for sessao in list_sessao_uf:
                yield Urna(self.id_pleito, *sessao)

    @staticmethod
    async def get_bu_file(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as request:
                data = await request.content.read()
                return data


    @staticmethod
    async def download(url, save_path):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as request:
                try:
                    os.makedirs(os.path.dirname(save_path))
                except FileExistsError:
                    pass
                file = await aiofiles.open(save_path, 'wb')
                await file.write(await request.content.read())
                # print("save_path", save_path)

    async def get_bu_data_hook_async(self, response):
        jsn = await AioHttpRequest.response_hook_json(response)
        urna = Urna(self.id_pleito, *response.url.path.split('/')[6:10])
        url_bu = urna.url_bu_from_json(jsn)

        data_bu = await self.get_bu_file(url_bu)

        return data_bu

    async def salva_bu_hook_async(self, response):
        jsn = await AioHttpRequest.response_hook_json(response)
        urna = Urna(self.id_pleito, *response.url.path.split('/')[6:10])
        url_bu = urna.url_bu_from_json(jsn)

        buf = BuFile(urna, path_raiz="C:/bu/")

        await self.download(url_bu, buf.path())

        # data_bu = requests.get(url_bu).content

        # BuFile(urna, path_raiz="C:/bu/").grava_arquivo(data_bu)

    def send(self, result):
        print("Pegou BU")
        pass

    def load_and_send(self, list_uf_list_sessao):

        urnas_requests = [
                             AioHttpRequest(urna.url_json_dados_urna,
                                            response_hook=self.get_bu_data_hook_async
                                            ) for urna in self.generator_urna(list_uf_list_sessao) if
                             not BuFile(urna, path_raiz="C:/bu/").pre_exist()][:]

        print("Qtd de urnas faltantes", len(urnas_requests))
        pprint(urnas_requests[:])
        urnas_retry = urnas_requests
        while urnas_retry:
            LOG.debug(f"Pegando dados de {len(urnas_retry)}")
            self.aiohttp.work(urnas_requests,
                              max_works=self.workers
                              )

            retry = []
            for aioreq in urnas_retry:
                if aioreq.exception:
                    print("FAIL: ", aioreq.url)
                    pprint(aioreq.tracebak)
                    aioreq.reset()
                    retry.append(aioreq)

                send_bu(aioreq.result)

            urnas_retry = retry
            pprint("##########  FAILS ##############")
            pprint(len(urnas_retry))
            if len(urnas_retry):
                LOG.debug("Aguardando 600s para reiniciar o processo")
                sleep(600)
                LOG.debug("reiniciando")

    def load_and_save_BUs(self, list_uf_list_sessao):

        urnas_requests = [
            AioHttpRequest(urna.url_json_dados_urna,
                           response_hook=self.salva_bu_hook_async
                           ) for urna in self.generator_urna(list_uf_list_sessao) if
                                  not BuFile(urna, path_raiz="C:/bu/").pre_exist()][:]

        print("Qtd de urnas faltantes", len(urnas_requests))
        pprint(urnas_requests[:])
        urnas_retry = urnas_requests
        while urnas_retry:
            LOG.debug(f"Pegando dados de {len(urnas_retry)}")
            self.aiohttp.work(urnas_requests,
                              max_works=self.workers
                              )

            retry = []
            for aioreq in urnas_retry:
                if aioreq.exception:
                    print("FAIL: ", aioreq.url)
                    pprint(aioreq.tracebak)
                    aioreq.reset()
                    retry.append(aioreq)

            urnas_retry = retry
            pprint("##########  FAILS ##############")
            pprint(len(urnas_retry))
            if len(urnas_retry):
                LOG.debug("Aguardando 600s para reiniciar o processo")
                sleep(600)
                LOG.debug("reiniciando")

    @log_in_out
    def work(self, list_estados_uf=None):

        if not list_estados_uf:
            list_estados_uf = self.lista_estados
        elif isinstance(list_estados_uf, str):
            list_estados_uf = (list_estados_uf,)

        list_uf_list_sessao = self.load_list_sessoes_list_uf(list_estados_uf)
        # pprint(list_uf_list_sessao)

        self.load_and_save_BUs(list_uf_list_sessao)


def test_bu_file_exist():
    urna = Urna('ba', 30694, 28, 406)
    print(urna)
    print(BuFile(urna, path_raiz="C:/bu/").pre_exist())


if __name__ == '__main__':
    rec = ResultadoEleicoesCrawler(
        "407", "https://resultados.tse.jus.br/oficial/ele2022/", workers=50
    )

    for uf in ResultadoEleicoesCrawler.lista_estados[:]:
        print(f"Pegando urnas de {uf}")
        rec.work(uf)


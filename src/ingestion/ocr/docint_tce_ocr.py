import requests
import json
from ingestion.ocr.base_ocr import BaseOcrProvider
from dotenv import load_dotenv
from settings import settings
from tenacity import retry, stop_after_attempt, wait_exponential
from utils import logger

load_dotenv()


class DocIntTceOCR(BaseOcrProvider):

    def __init__(self, cache_dir: str):
        super().__init__()
        self.__cache_dir = cache_dir
        self.__endpoint = settings.docint_endpoint
        self.__apikey = settings.docint_apikey

    @property
    def cache_dir(self):
        return self.__cache_dir

    @staticmethod
    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        # retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def _post_with_retry(endpoint, headers, files):
        response = requests.post(endpoint, headers=headers, files=files, verify=False, timeout=900)
        response.raise_for_status()
        return response

    def do_ocr(self, file_path: str):
        try:

            ## verificando se o arquivo existe:
            file_hash = self.get_str_hash(file_path)
            response = self.read_from_cache(file_hash)

            if (response is None):
                files = {'file': open(file_path, 'rb')}
                headers = {"authorization": f"Bearer {self.__apikey}"}
                logger.info(f"Chamando a API do TCE")
                response = self._post_with_retry(self.__endpoint, headers, files)

                if response.status_code == 200:
                    logger.info(f"Documento extraído!")
                    response = response.json()
                    self.save_to_cache(file_hash=file_hash, json_response=json.dumps(response))

            return response

        except Exception as ex:
            logger.error(f"Erro efetuando a requisição: {ex}")
            raise ex


if __name__ == '__main__':
    d = DocIntTceOCR(cache_dir="./output")
    d.do_ocr("./documento_teste.pdf")

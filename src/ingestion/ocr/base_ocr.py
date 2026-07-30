from abc import ABC, abstractmethod
import os
import json
import hashlib


class BaseOcrProvider(ABC):

    @abstractmethod
    def do_ocr(self, file_path:str):
        pass

    @property
    @abstractmethod    
    def cache_dir(self):
        pass
    
    def save_to_cache(self, file_hash:str, json_response: str):
        """
        Saves the resulting string to disk to avoid reprocessing same file
        """
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(f"{self.cache_dir}/{file_hash}.json", "a+") as file_cache:
            file_cache.write(json_response)     

    def read_from_cache(self, file_hash:str):
        """
        Load processed file form local disk 
        """

        if os.path.exists(f"{self.cache_dir}/{file_hash}.json"):
            with open(f"{self.cache_dir}/{file_hash}.json", "r") as f:
                return json.loads(f.read())
        else:
            return None
    def get_str_hash(self, filename:str):
        import utils
        return utils.get_str_hash(filename)
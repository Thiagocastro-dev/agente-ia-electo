from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document

class BaseRepository(ABC):

    @abstractmethod
    def store_document_list(self, documents: List[Document]):
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        pass
from repository.vector.base_repository import BaseRepository
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_qdrant import FastEmbedSparse, RetrievalMode
from settings import settings
from typing import List
import os

class QdrantRepository(BaseRepository):

    def __init__(self):
        client = QdrantClient(url=settings.qdrant_url)
        sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
        
        # Dynamically determine the embedding model and collection to avoid dimension mismatch
        if os.environ.get("GEMINI_API_KEY") and not settings.azure_api_key:
            from llm.gemini_embeddings import GeminiEmbeddings
            embed_model_instance = GeminiEmbeddings()
            vector_name = "gemini"
            collection_name = f"{settings.qdrant_collection}_gemini"
        else:
            from llm.langchain_azure import embed_model as azure_embed_model
            embed_model_instance = azure_embed_model
            vector_name = "openai"
            collection_name = settings.qdrant_collection

        self.__vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            embedding=embed_model_instance,
            sparse_embedding=sparse_embeddings,
            sparse_vector_name="bm25", 
            vector_name=vector_name,
            retrieval_mode=RetrievalMode.HYBRID
        )

    def store_document_list(self, documents: List[Document]):
        self.__vector_store.add_documents(documents)

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        return self.__vector_store.similarity_search(query, k=k)
        
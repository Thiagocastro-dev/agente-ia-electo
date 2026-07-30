from langchain_core.embeddings import Embeddings
from google import genai
import os
from typing import List

class GeminiEmbeddings(Embeddings):
    """
    Custom LangChain Embeddings implementation using the modern google-genai SDK.
    """
    def __init__(self, model: str = "gemini-embedding-2"):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=texts
            )
            return [emb.values for emb in result.embeddings]
        except Exception as e:
            import logging
            logging.error(f"Error in Gemini embed_documents: {e}")
            raise e

    def embed_query(self, text: str) -> List[float]:
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            import logging
            logging.error(f"Error in Gemini embed_query: {e}")
            raise e

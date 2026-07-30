from dotenv import load_dotenv
import os

load_dotenv()


class Settings:

    def __init__(self):
        ## TCE DOCINT
        self.docint_endpoint = os.environ.get("DOCINT_TCE_ENDPOINT", "")
        self.docint_apikey = os.environ.get("DOCINT_TCE_APY_KEY", "")

        ## QDRANT
        self.qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        self.qdrant_collection = os.environ.get("QDRANT_COLLECTION", "rag_collection")

        ## AZURE
        self.azure_api_key = os.environ.get("AZOPENAI_API_KEY", "")
        self.azure_endpoint = os.environ.get("AZOPENAI_API_ENDPOINT", "")
        self.azure_api_version = os.environ.get("AZOPENAI_API_VERSION", "2024-02-15-preview")
        self.azure_embbeding_model = os.environ.get("AZOPENAI_EMBEDDING_MODEL", "")

        ## POSTGRES
        self.postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
        self.postgres_port = os.environ.get("POSTGRES_PORT", "5432")
        self.postgres_user = os.environ.get("POSTGRES_USER", "postgres")
        self.postgres_password = os.environ.get("POSTGRES_PASS", "postgres")
        self.postgres_database = os.environ.get("POSTGRES_DATABASE", "postgres")
        self.postgres_schema = os.environ.get("POSTGRES_SCHEMA", "public")

        self.log_level = "INFO"
        
        ## APP
        
        self.ocr_engine = os.environ.get("OCR_ENGINE", "Docling")


settings = Settings()

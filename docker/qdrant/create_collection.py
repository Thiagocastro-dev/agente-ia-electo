from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
import os

load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.INFO, filename="programa.log", format="%(asctime)s - %(levelname)s - %(message)s")




collection_name = os.environ["QDRANT_COLLECTION"]

## configurações dos vetores. Se for usar outro modelo de embedding, tem que ajustar os parâmetros.


vectors_config={
    "openai": models.VectorParams(
        size=1536,
        distance=models.Distance.COSINE,
    )
}
sparse_vectors_config={
    "bm25": models.SparseVectorParams(
        modifier=models.Modifier.IDF,
    )
}


def create_index(collection:str, fieldname:str, schema:str ):
    try: 
        client.create_payload_index(
            collection_name=collection,
            field_name=fieldname,
            field_schema=schema
        )
    except Exception as error:
        logging.warning(f"Ocorreu um erro criando o índice: {error}")


client = QdrantClient(url=os.environ["QDRANT_URL"])


#Verificando se existe. Se não, cria 
if not client.collection_exists(collection_name):
    logging.warning(f"Criando a collection: {collection_name}")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=vectors_config,
        sparse_vectors_config=sparse_vectors_config
    )

    ## criando os índices:
    logging.info(f"Criando o índice: metadata.filename")
    create_index(collection=collection_name, fieldname="metadata.filename", schema="keyword" )
    
    logging.info(f"Criando o índice: metadata.page_number")
    create_index(collection=collection_name, fieldname="metadata.page_number", schema="integer" )
    
    logging.info(f"Criando o índice: metadata.kind")
    create_index(collection=collection_name, fieldname="metadata.kind", schema="keyword" )

else:
    logging.warning(f"Coleção {collection_name} já existe. Caso deseje recriar, acesso o dash do qdrant e exclua primeiro de lá e tente novamente")



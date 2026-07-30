import sys
import os
from typing import List

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from langchain_core.documents import Document
from repository.vector.qdrant_repository import QdrantRepository

def main():
    print("Iniciando ingestão do cardápio da Confeitaria Paola Electo...")
    
    # Check if cardapio file exists
    cardapio_path = "cardapio_paola_electo.md"
    if not os.path.exists(cardapio_path):
        print(f"Erro: Arquivo {cardapio_path} não encontrado!")
        sys.exit(1)
        
    with open(cardapio_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Split the markdown file by "---" to create logical chunks
    sections = content.split("---")
    
    documents = []
    filename = "cardapio_paola_electo.md"
    
    for i, section in enumerate(sections):
        section_text = section.strip()
        if not section_text:
            continue
            
        doc = Document(
            page_content=section_text,
            metadata={
                "filename": filename,
                "section_index": i + 1,
                "kind": "cardapio_doceria"
            }
        )
        documents.append(doc)
        
    print(f"Total de seções lidas para ingestão: {len(documents)}")
    
    # Store in Qdrant
    try:
        qdrant_repo = QdrantRepository()
        qdrant_repo.store_document_list(documents)
        print("Sucesso! Cardápio da Confeitaria Paola Electo ingerido no banco vetorial Qdrant com sucesso! 🎉")
    except Exception as e:
        print(f"Erro durante a ingestão do cardápio: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

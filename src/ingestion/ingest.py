from re import I
from ingestion.ocr.base_ocr import BaseOcrProvider
from ingestion.pdf_processor.process_pdf import PdfProcessor
import os
from ingestion.ocr.docint_tce_ocr import DocIntTceOCR
from PyPDF2 import PdfWriter
from langchain_core.documents import Document
import asyncio
from repository.vector.base_repository import BaseRepository
from typing import List
from repository.vector.qdrant_repository import QdrantRepository
import utils
from repository.relational.document_repository import DocumentRepository
from repository.relational.document_part_repository import DocumentPartRepository


class IngestPdf:

    def __init__(self, ocr_provider: BaseOcrProvider, pdf_processor: PdfProcessor, vector_repository: BaseRepository):
        self.__ocr_provider = ocr_provider
        self.__pdf_processor = pdf_processor
        self.__vector_repository = vector_repository
        self.__doc_repo = DocumentRepository()
        self.__part_repo = DocumentPartRepository()

    async def get_documents_from_pdf(self, pdf_file_path: str, filename: str):
        bookmarks = ['RTC', 'PARMPC']
        pdf_by_bookmarks = self.__pdf_processor.do_split(pdf_file_path=pdf_file_path, bookmarks=bookmarks)
        all_pages = []
        page_number = 1
        filehash = utils.get_str_hash(pdf_file_path)
        num_parts = sum([len(self.__pdf_processor.split_pdf(pdf['pdf'])) for pdf in pdf_by_bookmarks])
        # Register document in DB
        db_doc = self.__doc_repo.add_document(filehash, filename, state="processing", num_parts=num_parts)
        part_counter = 0
        for pdf in pdf_by_bookmarks:
            chunks = self.__pdf_processor.split_pdf(pdf['pdf'])
            pdf['metadata']['filename'] = filename
            pdf['metadata']['hash'] = filehash
            for chunk in chunks:
                # Register part in DB
                self.__part_repo.add_part(db_doc.id, part_counter, state="processing")
                try:
                    with open("temp.pdf", "wb") as f:
                        pdfWriter = PdfWriter()
                        for page in chunk:
                            pdfWriter.add_page(page)
                        pdfWriter.write(f)
                    ocr_response = self.__ocr_provider.do_ocr("temp.pdf")
                    os.remove("temp.pdf")
                    for page in ocr_response["pages"]:
                        doc = Document(
                            page_content=page,
                            metadata={
                                "filename": filename,
                                "page_number": page_number,
                                "kind": pdf['metadata']['bookmark']
                            }
                        )
                        page_number += 1
                        all_pages.append(doc)
                    # Update part as finished
                    self.__part_repo.update_part_state(db_doc.id, part_counter, state="finished")
                except Exception as ex:
                    import logging
                    logging.error(f"Error processing part {part_counter} of document {filename}: {ex}")
                    self.__part_repo.update_part_state(db_doc.id, part_counter, state="error")
                    self.__doc_repo.update_document_state(db_doc.id, state="error", processed_parts=part_counter)
                    break
                part_counter += 1
                # Update document processed_parts
                self.__doc_repo.update_document_state(db_doc.id, state="processing", processed_parts=part_counter)
        # Finalize document status
        self.__doc_repo.update_document_state(db_doc.id, state="finished", processed_parts=part_counter)
        return all_pages

    async def save_to_vector_store(self, documents: List[Document]):
        try:
            self.__vector_repository.store_document_list(documents=documents)
        except Exception as e:
            print(f"Failed to store pages for {documents[0].metadata['filename']}. Error: {e}")
            # Retry the batch
            for attempt in range(3):
                try:
                    self.__vector_repository.save_to_vector_store(documents=documents)
                    break
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed, retrying in 5 seconds...")
                    await asyncio.sleep(5)
            else:
                raise Exception(f"Failed to store pages for {documents[0].metadata['filename']}")


if __name__ == '__main__':
    d = IngestPdf(DocIntTceOCR(cache_dir="./output"), PdfProcessor(), QdrantRepository())
    docs = d.get_documents_from_pdf("./processo_TC_000004_2024_540858db_ee69_41fa_92b0_4d80bff1a2ed.pdf")
    asyncio.run(d.save_to_vector_store(docs))
    # print(docs)

import logging

from fastapi import APIRouter, UploadFile
from ingestion.pdf_processor.process_pdf import PdfProcessor
from ingestion.ocr.docint_tce_ocr import DocIntTceOCR
from ingestion.ocr.docling_ocr import DoclingOcr
from repository.vector.qdrant_repository import QdrantRepository
from ingestion.ingest import IngestPdf
from tempfile import NamedTemporaryFile
from fastapi import BackgroundTasks
import uuid
import os
from settings import settings

engines = {
    "AzureDocInt": DocIntTceOCR,
    "Docling": DoclingOcr            
}


class MyTask:

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = "pending"

    def update_status(self, status: str):
        self.status = status

    def get_status(self):
        return self.status

    def get_id(self):
        return self.task_id


router = APIRouter()

tasks = {}


@router.post("/ingestion", tags=["ingestion"])
def ingest_document(file: UploadFile, background_tasks: BackgroundTasks):
    task = MyTask(str(uuid.uuid4()))
    tasks[task.get_id()] = task
    # Save file synchronously
    from tempfile import NamedTemporaryFile
    temp_file_path = None
    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        for chunk in iter(lambda: file.file.read(1024 * 1024), b''):
            temp_file.write(chunk)
        temp_file_path = temp_file.name
    background_tasks.add_task(do_ingest, file.filename, temp_file_path, task)
    return task


@router.get("/task/{task_id}", tags=["tasks"])
async def get_task(task_id: str):
    return tasks.get(task_id)


def do_ingest(original_filename: str, temp_file_path: str, task: MyTask):
    import asyncio
    try:
        task.update_status("running")
        engine = engines[settings.ocr_engine]
        ingest = IngestPdf(engine(cache_dir="./output"), PdfProcessor(max_pages_per_chunk=80),
                              QdrantRepository())

        async def ingest_work():
            logging.info(f"Iniciando o processamento do documento {original_filename}")
            docs = await ingest.get_documents_from_pdf(temp_file_path, original_filename)
            await ingest.save_to_vector_store(docs)
            logging.info("Documento processado!")

        asyncio.run(ingest_work())
        task.update_status("completed")
    except Exception as e:
        task.update_status("failed")
        raise e
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


from PyPDF2 import PdfReader, PdfWriter
import math

class PdfProcessor:

    """
    Responsável por processar os PDFs para inserir no Qdrant
    """

    def __init__(self, max_pages_per_chunk:int = 100):        
        self.__max_pages_per_chunk = max_pages_per_chunk


    def do_split(self, pdf_file_path: str, **kwargs):
        return self.split_pdf_by_bookmarks(pdf_file_path,**kwargs)
 
    def split_pdf(self, pages):
        total_pages = len(pages)
        num_chunks = math.ceil(total_pages / self.__max_pages_per_chunk)
        
        chunks = []

        for chunk_index in range(num_chunks):
            start_idx = chunk_index * self.__max_pages_per_chunk
            end_idx = min((chunk_index + 1) * self.__max_pages_per_chunk, total_pages)
            chunk_pages = pages[start_idx:end_idx]
            chunks.append(chunk_pages)
        return chunks    
    
    def split_pdf_by_bookmarks(self, pdf_file, bookmarks):
        first_bookmark = True
        response = []
        for bookmark in bookmarks:
            if first_bookmark:
                pdf = self.get_pages_until_bookmark(pdf_file,bookmark)
                response.append({
                    "metadata": {
                        "bookmark": "PRE_"+bookmark
                    },
                    "pdf": pdf
                })
            pdf = self.get_pages_by_bookmark(pdf_file, bookmark)
            response.append({
                "metadata": {
                    "bookmark": bookmark
                },
                "pdf": pdf
            })
            first_bookmark = False
        return response

    def get_pages_until_bookmark(self, filename, nome_bookmark):
        """ Obtem as páginas de um documento até o bookmark informado"""
        input_pdf = PdfReader(f"{filename}")
        
        bookmark_encontrado = False
        pageend = False
        for bookmarks in input_pdf.outline:
            for bookmark in bookmarks:
                if(bookmark.title.startswith(nome_bookmark)):
                    pageend = bookmark.page.pdf.get_destination_page_number(bookmark) - 1 
                    bookmark_encontrado = True
                    break
        if not bookmark_encontrado:
            pageend = len(input_pdf.pages) - 1
        
        pages = []
        page_counter = 0
        
        for page in input_pdf.pages:
            if page_counter >= 0 and page_counter <= pageend:            
                pages.append(page)
            if page_counter >= pageend:
                break
            page_counter += 1

        return pages      
    
    def get_pages_by_bookmark(self, filename, nome_bookmark):
        input_pdf = PdfReader(f"{filename}")
        
        parecer_encontrado = False
        pagestart = False
        pageend = False
        for bookmarks in input_pdf.outline:
            for bookmark in bookmarks:
                if(bookmark.title.startswith(nome_bookmark)):
                    pagestart = bookmark.page.pdf.get_destination_page_number(bookmark) 
                    parecer_encontrado = True
                if parecer_encontrado is True and not bookmark.title.startswith(nome_bookmark):
                    pageend = bookmark.page.pdf.get_destination_page_number(bookmark) -1
                    break
            if pagestart and pageend:
                break
        
        if(not pagestart or not pageend):
            pagestart = 0
            pageend = len(input_pdf.pages) - 1
                    
        pages = []
        page_counter = 0
        
        for page in input_pdf.pages:
            if page_counter >= pagestart and page_counter <= pageend:            
                pages.append(page)
            if page_counter >= pageend:
                break
            page_counter += 1

        return pages     


if __name__ == "__main__":

    filename = "documento_teste.pdf"

    processor = PdfProcessor()

    parts = processor.split_pdf_by_bookmarks(f"{filename}", ['RTC', "PARMPC"])

    for part in parts:
        pdfWriter = PdfWriter()
        for page in part["pdf"]:
            pdfWriter.add_page(page)
        pdfWriter.write(f"{filename}-part-{part['metadata']['bookmark']}.pdf")

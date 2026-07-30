from itertools import accumulate
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat

from utils import logger
from ingestion.docling_custom.custom_markdown_serializer import CustomMarkdownDocSerializer

from ingestion.ocr.base_ocr import BaseOcrProvider



class DoclingOcr(BaseOcrProvider):
    def __init__(self, cache_dir: str, engine='easyocr'):
        format_options_dict = {
            'easyocr': {
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=self.__easyocr_pipeline_options()
                )
            }
        }

        self.converter = DocumentConverter(
            format_options=format_options_dict[engine],
        )

        self.__cache_dir = cache_dir

    def do_ocr(self, file_path: str):
        result = self.converter.convert(file_path)

        page_element_count = [1+len(i.assembled.elements) for i in result.pages]
        element_page_cutoff = list(accumulate([1] + page_element_count))
        pages = [
                (
                    CustomMarkdownDocSerializer.export_to_markdown_with_html_tables(
                        doc=result.document,
                        from_element=s,
                        to_element=e
                    )
                )  
                for s,e in zip(element_page_cutoff[:-1], element_page_cutoff[1:])
        ]

        document_to_parse = result.document

        markdown_output = "\n\n".join(pages)

        json_output = document_to_parse.export_to_dict()

        return {"markdown": markdown_output, "json": json_output, "pages": pages}

    @property
    def cache_dir(self):
        return self.__cache_dir

    def __easyocr_pipeline_options(self) -> PdfPipelineOptions:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        pipeline_options.ocr_options.lang = ["pt"]
        pipeline_options.generate_picture_images = True
        
        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=16, device=AcceleratorDevice.AUTO
        )

        return pipeline_options


if __name__ == "__main__":
    import json

    input_file = "documento_teste2.pdf"
    logger.info(f"Parsing {input_file}")
    parser = DoclingOcr(cache_dir='output')
    document = parser.do_ocr(input_file)
    # escrevendo o markdown no disco
    with open("output/markdown.md", "w") as f:
        f.write(document['markdown'])   

    # print(document)
    # print(document['markdown'])

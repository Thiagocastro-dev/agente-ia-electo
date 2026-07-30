import logging
import sys
from typing import Optional
import xml.etree.ElementTree as ET
from docling_core.types.doc.document import DoclingDocument ,ContentLayer, DOCUMENT_TOKENS_EXPORT_LABELS, DEFAULT_CONTENT_LAYERS
from docling_core.types.doc.labels import DocItemLabel
from docling_core.types.doc.base import ImageRefMode
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer, MarkdownParams
from docling_core.transforms.serializer.html import  HTMLTableSerializer
from docling_core.transforms.serializer.base import (
    BaseTableSerializer
)
import html
from utils import logger
from utils import extract_text_between_tags

# class MarkdownCustomImageSerializer(Markddow):
#     def __init__(self, doc:DoclingDocument, params:MarkdownParams):
#         super().__init__(doc = doc, params = params)


class CustomMarkdownDocSerializer(MarkdownDocSerializer):
    
    def __init__(self, doc:DoclingDocument, params:MarkdownParams):
        super().__init__(doc = doc, params = params)
        self.table_serializer: BaseTableSerializer = HTMLTableSerializer()
    
    @staticmethod
    def export_to_markdown_with_html_tables( 
        doc: DoclingDocument,
        delim: str = "\n\n",
        from_element: int = 0,
        to_element: int = sys.maxsize,
        labels: Optional[set[DocItemLabel]] = None,
        strict_text: bool = False,
        escape_underscores: bool = True,
        image_placeholder: str = "<!-- image -->",
        enable_chart_tables: bool = True,
        image_mode: ImageRefMode = ImageRefMode.PLACEHOLDER,
        indent: int = 4,
        text_width: int = -1,
        page_no: Optional[int] = None,
        included_content_layers: Optional[set[ContentLayer]] = None,
        page_break_placeholder: Optional[str] = None,  # e.g. "<!-- page break -->",
    ) -> str:
        from docling_core.transforms.serializer.markdown import (
            MarkdownParams,
        )

        my_labels = labels if labels is not None else DOCUMENT_TOKENS_EXPORT_LABELS
        my_layers = (
            included_content_layers
            if included_content_layers is not None
            else DEFAULT_CONTENT_LAYERS
        )
        serializer = CustomMarkdownDocSerializer(
            doc=doc,
            params=MarkdownParams(
                labels=my_labels,
                layers=my_layers,
                pages={page_no} if page_no is not None else None,
                start_idx=from_element,
                stop_idx=to_element,
                escape_underscores=escape_underscores,
                image_placeholder=image_placeholder,
                enable_chart_tables=enable_chart_tables,
                image_mode=image_mode,
                indent=indent,
                wrap_width=text_width if text_width > 0 else None,
                page_break_placeholder=page_break_placeholder,
            ),
        )
        ser_res = serializer.serialize()

        if delim != "\n\n":
            logger.warning(
                "Parameter `delim` has been deprecated and will be ignored.",
            )
        if strict_text:
            logger.warning(
                "Parameter `strict_text` has been deprecated and will be ignored.",
            )
        
        markdown_output = ser_res.text

        #formating tables as HTML
        tables = extract_text_between_tags(markdown_output,'table')

        for table in tables:
            txt_table = "<table>"+table+"</table>" 
            formatted = CustomMarkdownDocSerializer.format_xml_string(txt_table)
            markdown_output = markdown_output.replace(txt_table,formatted)

        return markdown_output
    
    @staticmethod
    def serialize_attrs( elem):
        if not elem.attrib:
            return ''
        return ' ' + ' '.join(f'{key}="{value}"' for key, value in elem.attrib.items())
    
    @staticmethod
    def format_xml_element( elem, level=0):
        indent = '  ' * level
        attrs = CustomMarkdownDocSerializer.serialize_attrs(elem)
        if len(elem) == 0:
            # No children
            text = (elem.text or '').strip()
            return f"{indent}<{elem.tag}{attrs}>{html.escape(text.strip())}</{elem.tag}>"
        else:
            lines = [f"{indent}<{elem.tag}{attrs}>"]
            if elem.text and elem.text.strip():
                lines[-1] = f"{lines[-1][:-1]}>{html.escape(elem.text.strip())}</{elem.tag}>"
                return '\n'.join(lines)
            for child in elem:
                lines.append(CustomMarkdownDocSerializer.format_xml_element(child, level + 1))
            lines.append(f"{indent}</{elem.tag}>")
            return '\n'.join(lines)
    
    @staticmethod
    def format_xml_string(xml_str):
        root = ET.fromstring(xml_str)
        return CustomMarkdownDocSerializer.format_xml_element(root)



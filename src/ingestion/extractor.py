# extractor.py
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption

class DocExtractor:
    def __init__(self):
        # OCR ve tablo tanıma gibi ağır işlemleri burada konfigüre edebilirsin
        options = PdfPipelineOptions()
        options.do_ocr = True 
        options.do_table_structure = True
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=options)
            }
        )

    def extract(self, source_path: str):
        print(f"[*] İşleniyor: {source_path}")
        result = self.converter.convert(source_path)
        return result.document  # Geriye zengin 'DoclingDocument' objesi döner
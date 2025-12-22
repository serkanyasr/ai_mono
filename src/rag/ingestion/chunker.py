# chunker.py
from docling.chunking import HybridChunker
from docling_core.types.doc import DoclingDocument

class DocChunker:
    def __init__(self):
        # HybridChunker hem hiyerarşiyi korur hem de token limitlerine uyar
        self.chunker = HybridChunker(
            tokenizer="sentence-transformers/all-MiniLM-L6-v2", # Embedding modelinle aynı olmalı
            max_tokens=512,
            merge_peers=True
        )

    def create_chunks(self, doc: DoclingDocument):
        print("[*] Chunking işlemi başladı...")
        chunks = self.chunker.chunk(doc)
        
        processed_chunks = []
        for chunk in chunks:
            # chunk.text: Metin içeriği
            # chunk.meta: Sayfa no, başlık yolu (breadcrumb) gibi bilgiler
            processed_chunks.append({
                "text": self.chunker.contextualize(chunk), # Metni üst başlıklarla zenginleştirir
                "metadata": chunk.meta.export_json_dict()
            })
        return processed_chunks
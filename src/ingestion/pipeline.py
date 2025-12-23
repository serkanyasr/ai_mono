# main.py
from extractor import DocExtractor
from chunker import DocChunker

def run_pipeline(pdf_path):
    # 1. ADIM: EXTRACTION (Docling ile PDF'i anla)
    extractor = DocExtractor()
    doc_object = extractor.extract(pdf_path)

    # 2. ADIM: CHUNKING (Docling ile akıllı parçala)
    chunker = DocChunker()
    chunks = chunker.create_chunks(doc_object)

    # 3. ADIM: INDEXING (Senin halledeceğin kısım)
    print(f"[*] Toplam {len(chunks)} chunk oluşturuldu. Indexleme başlıyor...")
    # indexer.save_to_vector_db(chunks) 
    
    # Test için ilk chunk'ı görelim
    if chunks:
        print("\n--- Örnek Chunk ---")
        print(f"İçerik: {chunks[0]['text'][:200]}...")
        print(f"Meta: {chunks[0]['metadata']}")

if __name__ == "__main__":
    run_pipeline("senin_dosyan.pdf")
# Script to ingest PDF brochures, extract text, compute embeddings, and build FAISS index.
import os
import sys
import re
from glob import glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.get_pdf_data import get_brand_model_year
from src.ingestion.chunker import extract_chunks
from src.ingestion.embedder import embed, format_pdf_chunk_qwen
from src.ingestion.faiss_store import build_faiss_index, save_index, save_metadata
from src.config import PDF_ROOT, VECTOR_STORE_DIR, FAISS_INDEX_PATH, METADATA_PATH, EMBEDDING_MODEL
import numpy as np

def build_corpus(pdf_path):
    meta = []
    chunks = []
    raw_chunks = extract_chunks(pdf_path)
    pdf_name = os.path.basename(pdf_path)
    brand, model, year = get_brand_model_year(pdf_name)
    for i, c in enumerate(raw_chunks):  
        chunk = format_pdf_chunk_qwen(c, pdf_name, brand, model, year)
        
        chunks.append(chunk)
        meta.append({
            "source": pdf_name,
            "brand": brand,
            "model": model,
            "year": year,
            "chunk_id": i,
            "text": c  
            
        })
    return chunks, meta

def main():
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

    print("\n[1] Chunking PDFs...")
    all_chunks = []
    all_meta = []
    for brand in os.listdir(PDF_ROOT):
        for pdf_file in glob(os.path.join(PDF_ROOT, brand, "*.pdf")):
            pdf_name = os.path.basename(pdf_file)
            print(f"  Processing: {pdf_name}")
            chunks, meta = build_corpus(pdf_file)
            
            if chunks is None:
                continue

            all_chunks.extend(chunks)
            all_meta.extend(meta)
            print(f"    Extracted {len(chunks)} chunks")
    print(f"Total chunks extracted: {len(all_chunks)}")
    

    print("\n[3] Computing embeddings...")
    print(f"  Using model: {EMBEDDING_MODEL}")
    embeddings = embed(all_chunks)
    print(f"  Shape: {embeddings.shape}")

    print("\n[4] Building FAISS index...")
    index = build_faiss_index(embeddings, metric="ip")
    print(f"  Index built with {index.ntotal} vectors")

    print("\n[5] Saving index and metadata...")
    save_index(index, FAISS_INDEX_PATH)
    save_metadata(all_meta, METADATA_PATH)
    print(f"  Index saved to: {FAISS_INDEX_PATH}")
    print(f"  Metadata saved to: {METADATA_PATH}")

    # create a file called finish.txt to indicate the process is complete
    with open(os.path.join(VECTOR_STORE_DIR, "finish.txt"), "w") as f:
        f.write("Ingestion complete")


if __name__ == "__main__":
    main()

# Script to ingest PDF brochures, extract text, compute embeddings, and build FAISS index.
import os
import sys
from glob import glob

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ingestion.chunker import extract_chunks
from src.ingestion.embedder import embed
from src.ingestion.faiss_store import build_faiss_index, save_index, save_metadata
from src.config import PDF_ROOT, VECTOR_STORE_DIR, FAISS_INDEX_PATH, METADATA_PATH, SENTENCE_TRANSFORMER_MODEL
import numpy as np


def build_corpus(pdf_path):
    meta = []
    chunks = extract_chunks(pdf_path)
    pdf_name = os.path.basename(pdf_path)
    split = pdf_name.replace(".pdf", "").split("_")
    brand = split[0]
    model = split[1].split()[1:]
    model = " ".join(model)
    year = split[2]
    for i, c in enumerate(chunks):  
            meta.append({
                "source": pdf_name,
                "brand": brand,
                "model": model,
                "year": year,
                "chunk_id": i,
                "text": c  
                
            })
    return chunks, meta


def normalize_embeddings(vecs):
    """Normalize embeddings for cosine similarity (IP metric)."""
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return vecs / norms


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
            all_chunks.extend(chunks)
            all_meta.extend(meta)
            print(f"    Extracted {len(chunks)} chunks")

    print("\n[3] Computing embeddings...")
    print(f"  Using model: {SENTENCE_TRANSFORMER_MODEL}")
    embeddings = embed(all_chunks)
    embeddings = embeddings.astype("float32")
    embeddings = normalize_embeddings(embeddings)
    print(f"  Shape: {embeddings.shape}")

    print("\n[4] Building FAISS index...")
    index = build_faiss_index(embeddings, metric="ip")
    print(f"  Index built with {index.ntotal} vectors")

    print("\n[5] Saving index and metadata...")
    save_index(index, FAISS_INDEX_PATH)
    save_metadata(all_meta, METADATA_PATH)
    print(f"  Index saved to: {FAISS_INDEX_PATH}")
    print(f"  Metadata saved to: {METADATA_PATH}")


if __name__ == "__main__":
    main()

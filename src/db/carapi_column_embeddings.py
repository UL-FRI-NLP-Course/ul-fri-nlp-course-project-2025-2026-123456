import os
import numpy as np
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.db.carapi_schema import CARAPI_SCHEMA_METADATA
from src.ingestion.embedder import embed_column
from src.db.carapi_queries import get_unique_values_from_column

# Carapi data column embeddings 
def format_column_text(metadata, example_values):
    parts = [
        f"Display name: {metadata.display_name}.",
        f"Column name: {metadata.name if hasattr(metadata, 'name') else ''}",
        f"Description: {metadata.description}.",
        f"Type: {metadata.data_type}.",
        f"Examples: {', '.join(example_values)}.",
        f"User intents: {', '.join(metadata.user_intents)}.",
        f"Synonyms: {', '.join(metadata.synonyms)}.",
        f"Related terms: {', '.join(metadata.related_terms)}.",
        f"Example queries: {', '.join(metadata.example_queries)}.",
    ]

    text = " ".join(parts)
    return text

def build_and_save_column_embeddings(model_name, embeddings_path, clear=False):

    if os.path.exists(embeddings_path) and not clear:
        return embeddings_path

    os.makedirs(os.path.dirname(embeddings_path), exist_ok=True)

    column_names = list(CARAPI_SCHEMA_METADATA.keys())

    vectors = []

    for idx, col in enumerate(column_names):
        metadata = CARAPI_SCHEMA_METADATA.get(col)

        example_values = get_unique_values_from_column(col, limit=metadata.sample_size)
        example_values = [str(v) for v in example_values if v is not None]
      
        text = format_column_text(metadata, example_values)
        vec = embed_column(text, model_name=model_name)

        vectors.append(vec)

    if not vectors:
        raise RuntimeError("No column embeddings were created.")

    emb_matrix = np.vstack(vectors).astype(np.float32)

    np.save(embeddings_path, emb_matrix)

    print(f"Saved column embeddings to {embeddings_path}")
    return embeddings_path


def load_column_embeddings(embeddings_path: str):
    if not os.path.exists(embeddings_path):
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}. Please run build_and_save_column_embeddings() first.")

    emb = np.load(embeddings_path)

    return emb, list(CARAPI_SCHEMA_METADATA.values())

def print_top_k_columns(scores: np.ndarray, tok_k: int =10):
    top_indices = np.argsort(scores)[::-1][:tok_k]

    column_names = list(CARAPI_SCHEMA_METADATA.keys())

    print(f"Top {tok_k} columns:")
    for idx in top_indices:
        column_name = column_names[idx]
        score = scores[idx]
        print(f" - {column_name}: {score:.4f}")
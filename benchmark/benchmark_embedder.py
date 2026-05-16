import numpy as np
from sentence_transformers import SentenceTransformer

import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

print(os.getcwd())

from src.db.carapi_schema import CARAPI_SCHEMA_METADATA
from src.db.carapi_queries import get_unique_values_from_column

_model_name = None
_embed_model = None

def get_model(model_name: str):
    global _embed_model, _model_name

    if _embed_model is None or _model_name != model_name:
        _model_name = model_name
        _embed_model = SentenceTransformer(_model_name)

    return _embed_model

def embed(texts, model_name: str = None):
    model = get_model(model_name)
    emb = model.encode(texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
    return np.array(emb, dtype=np.float32)


embedding_models = ['all-MiniLM-L6-v2', 
                    'BAAI/bge-base-en-v1.5', 
                    'BAAI/bge-large-en-v1.5', 
                    'intfloat/e5-base-v2', 
                    'intfloat/e5-large-v2',
                    'nomic-ai/nomic-embed-text-v1.5',
                    'thenlper/gte-large',]


def generate_column_embedding(column_name):
    metadata = CARAPI_SCHEMA_METADATA.get(column_name)
    if not metadata:
        raise ValueError(f"Column '{column_name}' not found in schema metadata.")
    

    example_values = get_unique_values_from_column(column_name, limit=metadata.sample_size)

    column_text = f"{metadata.display_name}. \
        Column name: {column_name}, \
        Description: {metadata.description}, \
        User intents: {', '.join(metadata.user_intents)}, \
        Synonims: {', '.join(metadata.synonyms)}, \
        Related terms: {', '.join(metadata.related_terms)}, \
        Value type: {metadata.value_type}, \
        Example queries: {', '.join(metadata.example_queries)}, \
        Sample values: {', '.join(example_values)}."

    print(f"Column text:\n{column_text}\n")


#def benchmark_embedder():


if __name__ == "__main__":
    generate_column_embedding("make")
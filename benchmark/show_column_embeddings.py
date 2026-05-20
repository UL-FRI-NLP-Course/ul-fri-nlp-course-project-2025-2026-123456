import os
import sys
import json
import numpy as np

from typing import List, Dict, Optional, Tuple

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.db.carapi_column_embeddings import load_column_embeddings
from src.ingestion.embedder import embed_query
from src.config import EMBEDDING_MODEL
from scripts.ingest_carapi_stats import build_and_save_column_embeddings


def load_json(file_path: str) -> List[str]:
    if file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)

    return data

def model_name_to_filename(model_name: str) -> str:
    if '/' in model_name:
        return model_name.split('/')[1]
    return model_name

def embeddings_path(model_name: str) -> str:
    benchmark_embeddings_dir = os.path.join(repo_root, "benchmark", "embeddings")
    model_filename = model_name_to_filename(model_name)
    embeddings_path = os.path.join(benchmark_embeddings_dir, f"{model_filename}.npy")
    return embeddings_path

def top_k_column_embeddings(model_name: str, queries_file: str, top_k: int = 5):
    build_and_save_column_embeddings(model_name=model_name, embeddings_path=embeddings_path(model_name))
    embeddings, metadata = load_column_embeddings(embeddings_path=embeddings_path(model_name))

    test_queries = load_json(queries_file)

    for query in test_queries:
        query_text = query['query']
        query_emb = embed_query(query_text, model_name=model_name)
        scores = np.dot(embeddings, query_emb)

        top_indices = np.argsort(scores)[::-1][:top_k]

        print(f"\nQuery: {query_text}")
        for idx in top_indices:
            column_name = metadata[idx].name
            score = scores[idx]
            print(f" - {column_name}: {score:.4f}")

def test_column_embeddings(model_name: str, queries_file: str, threshold: float):
    build_and_save_column_embeddings(model_name=model_name, embeddings_path=embeddings_path(model_name))
    embeddings, metadata = load_column_embeddings(embeddings_path=embeddings_path(model_name))

    test_queries = load_json(queries_file)

    for query in test_queries:
        query_text = query['query']
        query_emb = embed_query(query_text, model_name=model_name)
        scores = np.dot(embeddings, query_emb)

        top_indices = np.where(scores > threshold)[0]

        print(f"\nQuery: {query_text}")
        for idx in top_indices:
            column_name = metadata[idx].name
            score = scores[idx]
            print(f" - {column_name}: {score:.4f}")


if __name__ == "__main__":
    test_column_embeddings(EMBEDDING_MODEL, queries_file=os.path.join(repo_root, "benchmark", "queries_with_labeled_scores.json"), threshold=0.32)
    
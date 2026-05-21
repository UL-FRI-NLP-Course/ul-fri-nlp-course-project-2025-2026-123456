import os
import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import EMBEDDING_MODEL

"""
Supported embedding models:

Qwen/Qwen3-Embedding-0.6B
Qwen/Qwen3-Embedding-4B
BAAI/bge-large-en-v1.5 
BAAI/bge-m3
nomic-ai/nomic-embed-text-v1.5
thenlper/gte-large
google/embeddinggemma-300m
jinaai/jina-embeddings-v5-text-small
jinaai/jina-embeddings-v5-text-nano
"""

_model_name = None
_embed_model = None

def get_model(model_name: str = None):
    global _embed_model, _model_name

    if model_name is None:
        model_name = EMBEDDING_MODEL

    if _embed_model is None or _model_name != model_name:
        _embed_model = SentenceTransformer(model_name, trust_remote_code=True)
        _model_name = model_name

    return _embed_model

def embed(texts, model_name: str = None, **encode_kwargs):
    model = get_model(model_name)
    emb = model.encode(
        texts,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
        **encode_kwargs,
    )
    return np.array(emb, dtype=np.float32)

def init_embedder(model_name: str = None):
    get_model(model_name)
    print(f"Embedding model '{_model_name}' loaded successfully.\n")

def embed_query(query: str, model_name: str = None):
    if model_name is None:
        model_name = EMBEDDING_MODEL

    if model_name.startswith('Qwen'):
        formatted_query = format_query_qwen(query)
    elif model_name.startswith('BAAI/bge'):
        formatted_query = format_query_baai(query)
    elif model_name.startswith('nomic'):
        formatted_query = format_query_nomic(query)
    elif model_name.startswith('google'):
        formatted_query = format_query_gemma(query)
    elif model_name.startswith('jinaai'):
        return embed([query], model_name=model_name, task="retrieval", prompt_name="query")[0]
    else:
        formatted_query = query

    return embed([formatted_query], model_name=model_name)[0]

def embed_column(text: str, model_name: str = None):
    if model_name is None:
        model_name = EMBEDDING_MODEL

    if model_name.startswith('Qwen'):
        formatted_text = format_column_qwen(text)
    elif model_name.startswith('BAAI/bge'):
        formatted_text = format_column_baai(text)
    elif model_name.startswith('nomic'):
        formatted_text = format_column_nomic(text)
    elif model_name.startswith('google'):
        formatted_text = format_column_gemma(text)
    elif model_name.startswith('jinaai'):
        return embed([text], model_name=model_name, task="retrieval", prompt_name="document")[0]
    else:
        formatted_text = text

    return embed([formatted_text], model_name=model_name)[0]


def format_query_qwen(query: str) -> str:
    instruction = "Given a natural language query, identify the relevant columns from a vehicle database schema that would be useful for answering the query."
    return f"Instruct: {instruction}\nQuery: {query}"

def format_column_qwen(text: str) -> str:
    instruction = "Given a column from a vehicle database schema, represent the column in a way that captures its meaning and relevance for answering natural language queries about vehicles."
    return f"Instruct: {instruction}\n{text}"

def format_query_baai(query: str) -> str:
    return f"Represent this sentence for retrieving relevant vehicle database fields: {query}"

def format_column_baai(text: str) -> str:
    return f"Represent this sentence for retrieval: {text}"

def format_query_nomic(query: str) -> str:
    return f"search_query: {query}"

def format_column_nomic(text: str) -> str:
    return f"search_document:\n{text}"

def format_query_gemma(query: str) -> str:
    return f"task: search result | query: {query}"

def format_column_gemma(text: str) -> str:
    first_sentence = text.split(".")[0]
    title = first_sentence.split(":")[-1].strip()
    return f"title: {title} | text: {text}"
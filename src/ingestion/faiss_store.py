import faiss
import numpy as np
import os
import json


def build_faiss_index(embeddings: np.ndarray, metric='ip'):
    n, dim = embeddings.shape

    if metric == 'ip':
        index = faiss.IndexFlatIP(dim)
    else:
        index = faiss.IndexFlatL2(dim)

    index.add(embeddings)
    return index


def search_index(index, query_emb: np.ndarray, k=5):
    q = np.asarray(query_emb, dtype='float32')
    if q.ndim == 1:
        q = q.reshape(1, -1)
    scores, ids = index.search(q, k)
    return scores[0], ids[0]


def save_index(index, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    faiss.write_index(index, path)


def load_index(path):
    return faiss.read_index(path)


def save_metadata(meta, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def load_metadata(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

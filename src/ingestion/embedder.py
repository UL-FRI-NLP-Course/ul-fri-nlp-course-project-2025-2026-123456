import os
import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import EMBBEDDING_MODEL

_embed_model = None

def get_model(model_name: str = None):
    global _embed_model
    if _embed_model is None:
        model_name = model_name or EMBBEDDING_MODEL
        _embed_model = SentenceTransformer(model_name)
    return _embed_model

def embed(texts, model_name: str = None):
    model = get_model(model_name)
    emb = model.encode(texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
    return np.array(emb, dtype=np.float32)
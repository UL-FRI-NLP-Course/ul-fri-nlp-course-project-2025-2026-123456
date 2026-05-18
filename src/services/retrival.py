import numpy as np
from src.ingestion.faiss_store import load_index, load_metadata, search_index
from src.ingestion.embedder import embed
from src.config import FAISS_INDEX_PATH, METADATA_PATH
import os

_index = None
_metadata = None


def _load_index_and_metadata():
	global _index, _metadata

	if _index is None or _metadata is None:
		if not os.path.exists(FAISS_INDEX_PATH):
			raise FileNotFoundError(
				f"FAISS index not found at {FAISS_INDEX_PATH}. "
				f"Run: python3 scripts/ingest_pdfs.py"
			)
		_index = load_index(FAISS_INDEX_PATH)
		_metadata = load_metadata(METADATA_PATH)

	return _index, _metadata


def retrieve_candidates(parsed_query, k=10):
	# Embed the parsed query as a richer text query
	query_terms = []
	if isinstance(parsed_query, dict):
		query_terms.extend(parsed_query.get("terms", []))
		for key in ("fuel_types", "body_styles", "sizes", "use_cases"):
			query_terms.extend(parsed_query.get(key, []))
		budget_max = parsed_query.get("budget_max")
		if budget_max is not None:
			query_terms.append(f"budget under {budget_max}")
		seating_min = parsed_query.get("seating_min")
		if seating_min is not None:
			query_terms.append(f"{seating_min} seats")
		transmission = parsed_query.get("transmission")
		if transmission:
			query_terms.append(transmission)

	query_text = " ".join(query_terms).strip()
	if not query_text:
		query_text = "car recommendation"

	print(f"Query text: {query_text}\n")

	query = parsed_query.get("query", "")

	# in case of multiple queries:
	if isinstance(query, list):
		query = " ".join(query)

	query_emb = embed([query])[0]
	query_emb = query_emb.astype("float32")

	index, metadata = _load_index_and_metadata()
	scores, ids = search_index(index, query_emb, k=k)

	candidates = []
	context = []
	for score, idx in zip(scores, ids):
		meta = metadata[idx]
		vehicle_label = f"{meta.get('brand', '')} {meta.get('model', '')} {meta.get('year', '')}".strip()
		candidates.append({
			"source": meta["source"],
			"vehicle_label": vehicle_label,
			"chunk_id": meta["chunk_id"],
			"score": float(score),
		})
		# Load the actual chunk text
		chunk_text = meta.get("text", f"Chunk {meta['chunk_id']} from {meta['source']}")
		context.append(f"[{vehicle_label}] {chunk_text}")

	#print(f"Candidates retrieved: {candidates}\n")
	#print(f"Context: {context}\n")

	return candidates, context
import numpy as np
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
	sys.path.insert(0, root_dir)

from src.ingestion.faiss_store import load_index, load_metadata, search_index
from src.ingestion.embedder import embed, embed_conversation
from src.config import FAISS_INDEX_PATH, METADATA_PATH
from src.services.parser import parse_query

_index = None
_metadata = None

class RetrievalResult: 
	def __init__(self, brand=None, model=None, year=None, context=None, source=None):
		self.brand = brand
		self.model = model
		self.year = year
		self.context = context
		self.source = source


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

def create_conversation_text(user_queries, system_responses):
	merged = []
	for i in range(len(user_queries) + len(system_responses)):
		if i % 2 == 0 and user_queries:
			merged.append(f"User: {user_queries[i // 2]}")
		elif system_responses:
			merged.append(f"System: {system_responses[i // 2]}")
	return "\n".join(merged)

def retrieve_candidates(user_queries, system_responses, related_cars=None, k=10):
	related_car_labels = []
	for car in related_cars or []:
		related_car_labels.append(f"{car.get('brand', '')} {car.get('model', '')}")

	conversation_text = create_conversation_text(user_queries, system_responses)

	conv_embedding = embed_conversation(conversation_text, related_cars=related_car_labels)

	index, metadata = _load_index_and_metadata()
	scores, ids = search_index(index, conv_embedding, k=20)

	seen_models = set()
	unique_scores = []
	unique_ids = []
	for score, idx in zip(scores, ids):
		meta = metadata[idx]
		model = f"{meta.get('brand', '')} {meta.get('model', '')}".strip()
		# socres are orded from highest to lowest, so the first time we see a model is the one with the highest score
		if model not in seen_models:
			seen_models.add(model)
			unique_scores.append(score)
			unique_ids.append(idx)

	results = []

	for score, idx in zip(unique_scores, unique_ids):
		meta = metadata[idx]
		result = RetrievalResult(
			brand=meta.get("brand"),
			model=meta.get("model"),
			year=meta.get("year"),
			context=meta.get("text"),
			source=meta.get("source")
		)
		results.append(result)

	return results


if __name__ == "__main__":
	# Example usage
	user_queries = ['I am looking for an affordable family SUV with 7 seats.', 'I would like to have a diesel with consumption below 8L/100km.']
	system_responses = ['To help narrow down your options, could you please specify if you prefer a particular make or model? Additionally, do you have any specific requirements for fuel type or seating arrangement comfort?']
	related_cars = [{'brand': 'Audi', 'model': 'Q7'}, {'brand': 'Land Rover', 'model': 'Discovery'}, {'brand': 'Mercedes-Benz', 'model': 'GL-Class'}]
	
	retrieve_candidates(user_queries, system_responses, related_cars, k=5)
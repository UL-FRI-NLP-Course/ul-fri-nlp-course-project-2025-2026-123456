import re
import json
import os
import sys
from typing import Any, Dict
import numpy as np

src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
repo_root = os.path.abspath(os.path.join(src_dir, ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
# if src_dir not in sys.path:
#     sys.path.insert(0, src_dir)

from src.config import CARAPI_COLUMN_EMBEDDINGS_FILE, COLUMN_EMBEDDING_THRESHOLD
from src.services.llm import generate_json # , init_llm
from src.ingestion.embedder import embed_query
from src.db.carapi_column_embeddings import load_column_embeddings, print_top_k_columns
from src.db.carapi_schema import CARAPI_SCHEMA_METADATA
from src.db.carapi_queries import get_unique_values_from_column

COLUMN_EXTRACTION_SYSTEM_PROMPT = (
    "You are a structured data extraction assistant for a car search engine. "
    "You output ONLY valid JSON with no explanation, no markdown, no code fences."
)

def build_extraction_prompt(query, column):
    spec_lines = [
        f"Name : {column}",
        f"Display name: {CARAPI_SCHEMA_METADATA[column].display_name}.",
        f"Description : {CARAPI_SCHEMA_METADATA[column].description}.",
        f"Data type: {CARAPI_SCHEMA_METADATA[column].data_type}.",
    ]

    if CARAPI_SCHEMA_METADATA[column].unit:
        spec_lines.append(f"Unit: {CARAPI_SCHEMA_METADATA[column].unit}.")
    
    spec_lines.append(f"Synonyms: {', '.join(CARAPI_SCHEMA_METADATA[column].synonyms)}")

    sample_size = CARAPI_SCHEMA_METADATA[column].sample_size
    if sample_size is not None:
        sample_values = get_unique_values_from_column(column, limit=sample_size)
        spec_lines.append(f"Allowed values: {', '.join(str(v) for v in sample_values)}.")

    column_spec = "\n".join(spec_lines)

    prompt = f"""Extract the value for the database column below from the user query.

## Column definition
{column_spec}

## Constraint types
- "equal" - user wants exactly this value  (e.g. "7 seats", "sedan")
- "min"   - user wants at least this value  (e.g. "at least 5 seats")
- "max"   - user wants at most this value   (e.g. "under $30 000", "affordable")
- "range" - user gives a range; return value as [low, high]
- null    - this column cannot be determined from the query

## Rules
1. If the column value is clearly stated or strongly implied, extract it.
2. Vague words like "affordable" or "spacious" are NOT sufficient — set value and constraint to null.
3. If Allowed values are specified, the extracted value must be one of them.
4. Return ONLY the JSON object below, nothing else.

## User query
"{query}"

## Output format
{{"name": "{column}", "value": <extracted value or null>, "constraint": <"equal"|"min"|"max"|"range"|null>}}"""
    
    return prompt


def build_extraction_prompt_2(query, column):

    sample_size = CARAPI_SCHEMA_METADATA[column].sample_size
    if sample_size is not None:
        sample_values = get_unique_values_from_column(column, limit=sample_size)
        values = f"Allowed values: {', '.join(str(v) for v in sample_values)}."
        allowed_values = f"Extracted value must be one of the following: {', '.join(str(v) for v in sample_values)}."


    prompt = f"""Extract the value for the car database column {column} ({CARAPI_SCHEMA_METADATA[column].description}) from the user query.
    {allowed_values if sample_size is not None else ""}

Constraint types:
- "equal" - user wants exactly this value  (e.g. "7 seats", "sedan")
- "min"   - user wants at least this value  (e.g. "at least 5 seats")
- "max"   - user wants at most this value   (e.g. "under $30 000", "affordable")
- "range" - user gives a range; return value as [low, high]
- null    - this column cannot be determined from the query

If the value cannot be extracted with high confidence, return null for both value and constraint.

## User query
"{query}"

## Output format
{{"name": "{column}", "value": <extracted value or null>, "constraint": <"equal"|"min"|"max"|"range"|null>}}"""
    
    return prompt


def build_extraction_prompt_3(query, column):

    sample_size = CARAPI_SCHEMA_METADATA[column].sample_size
    if sample_size is not None:
        sample_values = get_unique_values_from_column(column, limit=sample_size)
        values = f"Allowed values: {', '.join(str(v) for v in sample_values)}."
        allowed_values = f"Extracted value(s) must be from the following list: {', '.join(str(v) for v in sample_values)}."


    prompt = f"""Extract the value and constraint for the car database column {column} ({CARAPI_SCHEMA_METADATA[column].description}) from the user query.
    {allowed_values if sample_size is not None else ""}

If the value cannot be extracted with high confidence, return null for both value and constraint.

## User query
"{query}"

## Output format
{{"name": "{column}", "value": <extracted value or null>, "constraint": <"equal"|"min"|"max"|"range"|null>}}"""
    
    return prompt

def extract_related_columns(query):
    embeddings, metadata = load_column_embeddings(embeddings_path=CARAPI_COLUMN_EMBEDDINGS_FILE)

    query_embedding = embed_query(query)

    assert embeddings.shape[1] == query_embedding.shape[0], \
        f"Embedding mismatch: {embeddings.shape[1]} vs {query_embedding.shape[0]}"

    scores = np.dot(embeddings, query_embedding)

    accepted_indices = np.where(scores > COLUMN_EMBEDDING_THRESHOLD)[0]
    related_columns = [metadata[idx].name for idx in accepted_indices]

    return related_columns


def parse_query(query: str, zacasni_idx: int = 1):

    # if zacasni_idx == 1:

    #     sample = [
    #         {'name': 'body_type', 'value': 'SUV', 'constraint': 'equal'},
    #         {'name': 'seats', 'value': None, 'constraint': 'min'},
    #         {'name': 'fuel_type', 'value': 'electric', 'constraint': 'equal'},
    #         {'name': 'combined_l_per_100km', 'value': None, 'constraint': None},
    #     ]

    # elif zacasni_idx == 2:
    #     sample = [
    #         {'name': 'seats', 'value': '5', 'constraint': 'min'}
    #     ]
    # else: 

    #     sample = [
    #         {'name': 'combined_l_per_100km', 'value': None, 'constraint': None}
    #     ]
        
    # return sample

    related_columns = extract_related_columns(query)

    column_fields = []

    for column in related_columns:
        prompt = build_extraction_prompt_2(query, column)
        response = generate_json(COLUMN_EXTRACTION_SYSTEM_PROMPT, prompt, column)
        column_fields.append(response)

    return column_fields

def format_parsed_response(response):
    for r in response:
        name = r.get("name")
        value = r.get("value")
        constraint = r.get("constraint")
        print(f"{name:>20}: {value} ({constraint})")

if __name__ == "__main__":
    init_llm()

    query = "I want an affordable familiy SUV with 7 seats."
    print(f"Query: {query}")
    response = parse_query(query)
    format_parsed_response(response)
    print()

    query = "I am on a strict budget, so I am looking for something under 20k. USD"
    print(f"Query: {query}")
    response = parse_query(query)
    format_parsed_response(response)
    print()

    query = "I want a sporty coupe with at least 300 hp and rear wheel drive."
    print(f"Query: {query}")
    response = parse_query(query)
    format_parsed_response(response)
    print()

    query = "I'm looking for a spacious SUV under 30.000 USD with low consumption, preferably electric or hybrid, for family road trips. It should have at least 5 seats and an automatic transmission."
    print(f"Query: {query}")
    response = parse_query(query)
    format_parsed_response(response)
    print()

    query = "Truck with good towing capacity, preferably diesel, for off-road and road trips, budget up to 50k."
    print(f"Query: {query}")
    response = parse_query(query)
    format_parsed_response(response)
    print()
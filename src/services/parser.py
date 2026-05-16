import re
import json
import os
import sys
from typing import Any, Dict

src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
repo_root = os.path.abspath(os.path.join(src_dir, ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.services.llm import generate_response

_BUDGET_PATTERNS = [
    #re.compile(r"(?:budget|price|cost|spend(?:ing)?)\s*(?:is|of|around|about|under|below|max(?:imum)?)?\s*[$€£]?\s*(\d{1,3}(?:[.,]\d{3})*|\d+)(?:\s*(k|thousand))?", re.I),
    #re.compile(r"[$€£]\s*(\d{1,3}(?:[.,]\d{3})*|\d+)(?:\s*(k|thousand))?", re.I),
    #re.compile(r"(\d{1,3}(?:[.,]\d{3})*|\d+)\s*(k|thousand)\s*(?:euros?|dollars?|usd|eur)?", re.I),
    # ^ doesnt work if i put 1000 (?)
    # added "up to" and "e"
    re.compile(r"(?:budget|price|cost|spend(?:ing)?)\s*(?:is|of|around|about|under|below|max(?:imum)?|up to)?\s*[$€£]?\s*(\d+(?:[.,]\d+)?)(?:\s*(k|thousand))?", re.I),
    re.compile(r"[$€£]\s*(\d+(?:[.,]\d+)?)(?:\s*(k|thousand))?", re.I),
    re.compile(r"(\d+(?:[.,]\d+)?)(?:\s*(k|thousand))\s*(?:euros?|dollars?|usd|eur|e)?", re.I),
]

_FUEL_KEYWORDS = {
    "electric": ["electric", "ev", "battery electric", "bev"],
    "hybrid": ["hybrid", "phev", "plug-in hybrid", "plug in hybrid"],
    "diesel": ["diesel"],
    "petrol": ["petrol", "gasoline", "gas"],
}

_BODY_STYLES = {
    "suv": ["suv", "crossover", "cross-over"],
    "sedan": ["sedan", "saloon", "limousine"],
    "hatchback": ["hatchback", "hatch"],
    "wagon": ["wagon", "estate", "touring"],
    "coupe": ["coupe", "coupé"],
    "van": ["van", "mpv", "minivan", "people mover"],
    "pickup": ["pickup", "pick-up", "truck"],
}

_SIZE_KEYWORDS = {
    "small": ["small", "compact", "city", "urban"],
    "medium": ["medium", "mid-size", "midsize", "family"],
    "large": ["large", "big", "full-size", "spacious"],
}

_USE_CASE_KEYWORDS = {
    "family": ["family", "kids", "child", "child seat"],
    "city": ["city", "urban", "commute", "commuting"],
    "road_trip": ["road trip", "travel", "long distance", "highway"],
    "offroad": ["offroad", "off-road", "4x4", "all terrain"],
    "sport": ["sport", "fast", "performance", "fun to drive"],
}



def _extract_budget(query: str):
    for pattern in _BUDGET_PATTERNS:
        match = pattern.search(query)
        if not match:
            continue

        raw_value = match.group(1).replace(",", "").replace(" ", "")
        multiplier = match.group(2)
        value = float(raw_value)
        if multiplier and multiplier.lower() in {"k", "thousand"}:
            value *= 1000
        return int(value)

    return None


def _find_keywords(query: str, keyword_map: dict):
    found = []
    lower_query = query.lower()
    for label, variants in keyword_map.items():
        for variant in variants:
            if variant in lower_query:
                found.append(label)
                break
    return found


def extract_consumption(query):

    p1 = r"(low|small|minimal)\s+consumption"
    p2 = r"consumption\s*(?:is|of|around|about|under|below|max(?:imum)?|up to)?\s*(\d+(?:\.\d+)?)\s*l(?:/100km)?"

    # search if user provided adjective (small...) and set manually consumption to idk, 4L/100km
    match = re.search(p1, query)

    if match:

        # delete these words from query so that they don't get mixed up with other extractions
        full_match = match.group(0)
        cleaned_query = query.replace(full_match, "")

        consumption_value = 4.0

        return consumption_value, cleaned_query

    # search if user provided a maximum number of consumption
    match = re.search(p2, query)
    if match:

        consumption_value = float(match.group(1))

        # delete these words from query so that they don't get mixed up with other extractions
        full_match = match.group(0)
        cleaned_query = query.replace(full_match, "")

        return consumption_value, cleaned_query


    return None, query


def parse_query(query: str):
    normalized = query.strip()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    schema_path = os.path.join(repo_root, "data", "carapi_schema.json")
    schema = {}
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as fh:
            schema = json.load(fh)

    prompt = (
        "You are a JSON extractor. Given a user's natural-language car query and a "
        "schema (JSON) describing available fields, extract the intent and produce a "
        "JSON object mapping field names to values. Only include keys that appear in "
        "the schema. Use types: number for numeric fields, string for free text, list "
        "for categorical multiple values. If a field is not mentioned, omit it or set "
        "it to null. Return ONLY valid JSON (no surrounding explanation).\n\n"
        f"Schema: {json.dumps(schema, ensure_ascii=False)}\n\n"
        f"User query: {normalized}\n\n"
        "Output:"
    )

    print(json.dumps(schema, ensure_ascii=False))

    llm_out = generate_response(prompt)

    print(f"LLM output: {llm_out}")

    # extract the first JSON object in the LLM output
    start = llm_out.find("{")
    end = llm_out.rfind("}")
    if start != -1 and end != -1 and end > start:
        json_text = llm_out[start:end+1]
        parsed = json.loads(json_text)

        # Normalize some common fields expected by the system
        # Ensure `query` and `terms` exist
        parsed.setdefault("query", normalized)
        if "terms" not in parsed:
            parsed["terms"] = [normalized]

        return parsed

def heuristic_parse_query(normalized: str) -> Dict[str, Any]:
    lower = normalized.lower()

    # adding consumption and also delete part of consumption out of query
    # because before it didn't work for smth like "big car and small consumption" -> sizes=[big, small]
    max_consumption, removed_adj = extract_consumption(lower)

    budget_max = _extract_budget(normalized)
    fuel_types = _find_keywords(lower, _FUEL_KEYWORDS)
    body_styles = _find_keywords(lower, _BODY_STYLES)
    sizes = _find_keywords(removed_adj, _SIZE_KEYWORDS)
    use_cases = _find_keywords(lower, _USE_CASE_KEYWORDS)

    seating_min = None
    seat_match = re.search(r"(\d{1,2})\s*(?:seats?|seat|people|passengers?)", lower)
    if seat_match:
        seating_min = int(seat_match.group(1))

    transmission = None
    if any(term in lower for term in ["automatic", "auto"]):
        transmission = "automatic"
    elif any(term in lower for term in ["manual"]):
        transmission = "manual"

    terms = [normalized]
    for bucket in (fuel_types, body_styles, sizes, use_cases):
        terms.extend(bucket)

    if budget_max is not None:
        terms.append(f"budget {budget_max}")

    return {
        "query": normalized,
        "budget_max": budget_max,
        "fuel_types": fuel_types,
        "body_styles": body_styles,
        "sizes": sizes,
        "use_cases": use_cases,
        "seating_min": seating_min,
        "transmission": transmission,
        "terms": terms,
    }

if __name__ == "__main__":
    user_query = "I'm looking for a spacious SUV under $30k with low consumption, preferably electric or hybrid, for family road trips. It should have at least 5 seats and an automatic transmission."
    parsed = parse_query(user_query)
    print(json.dumps(parsed, indent=2, ensure_ascii=False))

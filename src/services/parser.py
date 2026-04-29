import re

_BUDGET_PATTERNS = [
    re.compile(r"(?:budget|price|cost|spend(?:ing)?)\s*(?:is|of|around|about|under|below|max(?:imum)?)?\s*[$€£]?\s*(\d{1,3}(?:[.,]\d{3})*|\d+)(?:\s*(k|thousand))?", re.I),
    re.compile(r"[$€£]\s*(\d{1,3}(?:[.,]\d{3})*|\d+)(?:\s*(k|thousand))?", re.I),
    re.compile(r"(\d{1,3}(?:[.,]\d{3})*|\d+)\s*(k|thousand)\s*(?:euros?|dollars?|usd|eur)?", re.I),
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


def parse_query(query: str):
    """Parse the user query into retrieval and ranking signals.

    Returns a compact dict with structured preferences and a list of search terms
    that can be used to enrich retrieval.
    """
    normalized = query.strip()
    lower = normalized.lower()

    budget_max = _extract_budget(normalized)
    fuel_types = _find_keywords(lower, _FUEL_KEYWORDS)
    body_styles = _find_keywords(lower, _BODY_STYLES)
    sizes = _find_keywords(lower, _SIZE_KEYWORDS)
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

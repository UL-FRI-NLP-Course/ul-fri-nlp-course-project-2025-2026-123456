from src.services.parser import parse_query
from src.services.retrival import retrieve_candidates
from src.services.ranking import rank_cars
from src.services.llm import generate_response
from src.db.carapi_queries import (
    query_carapi_by_constraints,
    get_all_carapi_cars,
    cars_to_dicts,
)
from src.services.conversation import make_conversation

PERSONA = (
    "You are a friendly, expert car salesperson. Give concise, practical advice "
    "tailored to the user's needs. Mention tradeoffs and cite brief evidence "
    "from the provided context when relevant."
)

INSTRUCTIONS = (
    "Answer as a helpful car salesperson in ~150-300 words. Start with a 1-line summary."
    "If the user query is not car related, respond that you can only answer car-related questions."
)

TOO_BROAD_THRESHOLD = 20
CONSTRAINTS_IMPORTANCE = [
    "budget_max",
    "body_styles",
    "fuel_types",
    "seating_min",
    "sizes",
    "transmission",
    "use_cases",
]

def generate_prompt(query: str, parsed: dict, ranked: list, context: list):
    top_cars = ranked[:3]
    rec_text = "\n".join(
        [f"- {c.get('make', '')} {c.get('model', '')} ({c.get('year', '')}) (score={c.get('score', 0):.2f})"
         for c in top_cars]
    )

    ctx_text = "\n---\n".join(context[:5]) if context else ""

    prompt = (
        f"{PERSONA}\n\nUser query: {query}\n\n"
        f"Top recommendations:\n{rec_text}\n\n"
        f"Context snippets (each snippet is tagged with the vehicle it belongs to):\n{ctx_text}\n\n"
        f"{INSTRUCTIONS}"
    )

    return prompt


def generate_raw_prompt(query: str):
    return (
        f"{PERSONA}\n\n"
        f"User query: {query}\n\n"
        f"{INSTRUCTIONS}"
    )


def handle_query(query: str):

    # -------------------------
    # Step 1: Parse query
    # -------------------------
    parsed_list = parse_query(query)

    # Normalize into dict (SAFE + CONSISTENT FORMAT)
    parsed = {}

    for item in parsed_list:

        if not isinstance(item, dict):
            continue

        name = item.get("name")
        if not name:
            continue

        parsed[name] = {
            "value": item.get("value"),
            "constraint": item.get("constraint")
        }

    print(f"Query: {query}\n")
    print(f"Parsed query: {parsed}\n")

    # -------------------------
    # Step 2: DB Query
    # -------------------------
    db_cars = query_carapi_by_constraints(parsed, limit=20)
    db_cars_list = cars_to_dicts(db_cars)

    print(f"extracted constraints:\n{parsed}")
    print(f"extracted {len(db_cars_list)} cars")

    # -------------------------
    # Count missing constraints properly
    # -------------------------
    empty_constraints = 0

    for key, value in parsed.items():
        if value is None:
            empty_constraints += 1
        elif isinstance(value, dict):
            if value.get("value") in (None, "", []):
                empty_constraints += 1

    print(f"number of empty constraints: {empty_constraints}")

    # -------------------------
    # Case 1: no matches
    # -------------------------
    if len(db_cars_list) == 0:
        return {
            "recommendations": [],
            "response": (
                "I couldn't find cars matching all your requirements. "
                "Try increasing your budget or relaxing some constraints."
            )
        }

    # -------------------------
    # Case 2: too broad + missing info
    # -------------------------
    if len(db_cars_list) > TOO_BROAD_THRESHOLD and empty_constraints >= 2:
        return make_conversation(parsed)

    # -------------------------
    # Step 3: FAISS retrieval
    # -------------------------
    candidates, context = retrieve_candidates(parsed, k=10)

    # -------------------------
    # Step 4: Merge FAISS scores
    # -------------------------
    faiss_scores = {
        c.get("source", ""): c.get("score", 0.0)
        for c in candidates
        if isinstance(c, dict)
    }

    # Attach FAISS score safely
    for car in db_cars_list:
        source_key = f"{car.get('brand', '')} {car.get('model', '')}"
        car["faiss_score"] = min(faiss_scores.get(source_key, 0.3), 1.0)

    # -------------------------
    # Fallback if DB empty
    # -------------------------
    if not db_cars_list:
        db_cars_list = get_all_carapi_cars(limit=20)

    # -------------------------
    # Step 5: Ranking
    # -------------------------
    ranked = rank_cars(db_cars_list, parsed)

    # -------------------------
    # Step 6: LLM response
    # -------------------------
    prompt = generate_prompt(query, parsed, ranked, context)
    response = generate_response(prompt)

    return {
        "recommendations": ranked[:3],
        "response": response
    }


def handle_query_raw_llm(query: str):
    prompt = generate_raw_prompt(query)
    response = generate_response(prompt)
    return {
        "recommendations": [],
        "response": response,
    }
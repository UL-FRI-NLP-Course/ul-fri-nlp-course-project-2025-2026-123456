from src.services.parser import parse_query
from src.services.retrival import retrieve_candidates
from src.services.ranking import rank_cars
from src.services.llm import generate_response
from src.db.carapi_queries import (
    query_carapi_by_constraints,
    get_all_carapi_cars,
    cars_to_dicts,
)

PERSONA = (
    "You are a friendly, expert car salesperson. Give concise, practical advice "
    "tailored to the user's needs. Mention tradeoffs and cite brief evidence "
    "from the provided context when relevant."
)

INSTRUCTIONS = (
    "Answer as a helpful car salesperson in ~150-300 words. Start with a 1-line summary."
    "If the user query is not car related, respond that you can only answer car-related questions."
)


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
    # Step 1: Parse query
    parsed = parse_query(query)
    print(f"Query: {query}\n")
    print(f"Parsed query: {parsed}\n")

    # Step 2: Query DB for cars matching constraints
    db_cars = query_carapi_by_constraints(parsed, limit=20)
    db_cars_list = cars_to_dicts(db_cars)

    # Step 3: Retrieve FAISS context based on parsed query terms
    candidates, context = retrieve_candidates(parsed, k=10)

    # Step 4: Build a mapping of FAISS candidate sources to cars
    # and merge DB results with FAISS scores
    faiss_scores = {c.get("source", ""): c.get("score", 0.0) for c in candidates}

    # Combine DB cars with FAISS scores
    # (cars from DB are already filtered by constraints)
    for car in db_cars_list:
        source_key = f"{car.get('brand', '')} {car.get('model', '')}"
        # Normalize FAISS score to [0, 1]
        car["faiss_score"] = min(faiss_scores.get(source_key, 0.3), 1.0)

    # If no DB matches, broaden to the full CarAPI dataset.
    if not db_cars_list:
        db_cars_list = get_all_carapi_cars(limit=20)

    # Step 5: Rank combined results
    ranked = rank_cars(db_cars_list, parsed)

    # Step 6: Generate response
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
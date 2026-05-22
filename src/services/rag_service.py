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
from src.services.conversation import ConversationState

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

    print(f"top cars:\n{top_cars}")
    print(f"rec text:\n{rec_text}")
    print(f"ctx text:\n{ctx_text}")
    print(f"final prompt:\n{prompt}")

    return prompt

# POSSIBLE PROMPT ker un zgori si loh mal zmisluje 
"""
    You are a conversational car recommendation assistant. You are talking directly 
    to the user, and their preferences matched with the following three cars:
    
    1. 'id': 9023, 'brand': 'Toyota', 'model': 'Yaris', 'year': 2020, 'trim': 'L', 'series': None, 'submodel': 'L', 'msrp': 15650.0, 'fuel_type': 'regular unleaded', 'body_type': 'Sedan', 'seats': 5, 'transmission': '6-speed manual', 'horsepower': 106, 'torque_nm': 140, 'fuel_consumption_l_per_100km': 6.92, 'width_cm': 169, 'length_cm': 435, 'height_cm': 149, 'weight_kg': 1082, 'trunk_volume': 382, 'has_awd': False
    2. 'id': 9025, 'brand': 'Toyota', 'model': 'Yaris', 'year': 2020, 'trim': 'LE', 'series': None, 'submodel': 'LE', 'msrp': 16650.0, 'fuel_type': 'regular unleaded', 'body_type': 'Sedan', 'seats': 5, 'transmission': '6-speed manual', 'horsepower': 106, 'torque_nm': 140, 'fuel_consumption_l_per_100km': 6.92, 'width_cm': 169, 'length_cm': 435, 'height_cm': 149, 'weight_kg': 1089, 'trunk_volume': 382, 'has_awd': False
    3. 'id': 9024, 'brand': 'Toyota', 'model': 'Yaris', 'year': 2020, 'trim': 'L', 'series': None, 'submodel': 'L', 'msrp': 16750.0, 'fuel_type': 'regular unleaded', 'body_type': 'Sedan', 'seats': 5, 'transmission': '6-speed automatic', 'horsepower': 106, 'torque_nm': 140, 'fuel_consumption_l_per_100km': 6.72, 'width_cm': 169, 'length_cm': 435, 'height_cm': 149, 'weight_kg': 1103, 'trunk_volume': 382, 'has_awd': False
    
    You need to list these three options, and then explain briefly what is the 
    main difference between all three of them.

    Do NOT write anything besides the options and their differences. 
    You MUST respond in natural language only.
    Do NOT output code, functions, JSON, or pseudocode.


    You MUST respond in this format:
    Option 1: ...
    Option 2: ...
    Option 3: ...
    Difference: ...

"""   

def generate_raw_prompt(query: str):
    return (
        f"{PERSONA}\n\n"
        f"User query: {query}\n\n"
        f"{INSTRUCTIONS}"
    )


def handle_query(query: str, state: ConversationState):

    
    # create a conversation between user and LLM
    # that will get as many info for DB cars as possible
    #status, parsed, merge_parsed, db_cars_list, llm_response = make_conversation(query, state)
    state = make_conversation(query, state)

    # If conversation is not finished → return early
    if state.status == "NOT READY":
        return state, []

    #print(f"FINAL STATE")
    #state.print_info()

    print("BEFORE RETRIEVE CANDIDATES")

    # Step 3: Retrieve FAISS context based on parsed query terms
    candidates, context = retrieve_candidates(state.query_parsed, state.queries, k=10)

    print("BEFORE FAISS SCORES")

    # Step 4: Build a mapping of FAISS candidate sources to cars
    # and merge DB results with FAISS scores
    faiss_scores = {c.get("source", ""): c.get("score", 0.0) for c in candidates}

    print("BEFORE FOR LOOP")


    # Combine DB cars with FAISS scores
    # (cars from DB are already filtered by constraints)
    for car in state.db_cars_list:
        source_key = f"{car.get('brand', '')} {car.get('model', '')}"
        # Normalize FAISS score to [0, 1]
        car["faiss_score"] = min(faiss_scores.get(source_key, 0.3), 1.0)

    # If no DB matches, broaden to the full CarAPI dataset.
    if not state.db_cars_list:
        state.db_cars_list = get_all_carapi_cars(limit=20)

    print("BEFORE RANK CARS")

    # Step 5: Rank combined results
    ranked = rank_cars(state.db_cars_list, state.query_parsed)

    # Step 6: Generate response
    queries_joined = "\n".join([f"User: {q}" for q in state.queries])
    #print(f"QUERIES JOINED:\n{queries_joined}")
    prompt = generate_prompt(queries_joined, state.query_parsed, ranked, context)
    response = generate_response(prompt)

    state.llm_response = response

    return state, ranked[:3]


def handle_query_raw_llm(query: str):
    prompt = generate_raw_prompt(query)
    response = generate_response(prompt)
    return {
        "recommendations": [],
        "response": response,
    }
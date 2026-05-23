from src.services.retrival import create_conversation_text, retrieve_candidates
from src.services.llm import generate_response
from src.db.carapi_queries import (
    get_most_similar_value_in_column,
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

def generate_prompt(conversation: str, car_recommendations: list, context: list):
    recommended_text = ""
    for i, car in enumerate(car_recommendations):
        recommended_text += f"{i+1}. {car.get('brand', '')} {car.get('model', '')}\n"

    context_list = []
    for item in context:
        single_chunk = f"Source: {item.source}\nBrand: {item.brand}\nModel: {item.model}\nContext: {item.context}\n\n"
        context_list.append(single_chunk)

    context_text = "\n".join(context_list)


    prompt = (
        f"{PERSONA}\n\nConversation: {conversation}\n\n"
        f"Recommendations:\n{recommended_text}\n\n"
        f"Context snippets (each snippet is tagged with the vehicle it belongs to):\n{context_text}\n\n"
        f"{INSTRUCTIONS}"
    )

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


def merge_database_cars_with_retrieval_results(db_cars, retrieval_results):
    def car_identifier(brand, model):
        identifier = f"{brand}{model}"
        identifier = ''.join(e for e in identifier if e.isalnum()).lower()
        return identifier

    merged = []
    unique_cars = set()
    for car in db_cars: 
        brand = car.get('brand', '')
        model = car.get('model', '')

        identifier = car_identifier(brand, model)
            
        if identifier not in unique_cars:
            unique_cars.add(identifier)
            merged.append({
                'brand': brand,
                'model': model,
            })

    for result in retrieval_results:
        brand = result.brand
        model = result.model

        identifier = car_identifier(brand, model)

        if identifier not in unique_cars:
            unique_cars.add(identifier)
            merged.append({
                'brand': brand,
                'model': model,
            })

    return merged


def filter_retrived_results_by_constraints(retrieved_results, constraints):
    filtered = []
    for result in retrieved_results:
        brand = get_most_similar_value_in_column("make", result.brand)[0]
        if not brand:
            continue
        
        model = get_most_similar_value_in_column("model", result.model)[0]
        if not model:
            continue

        new_constraint = {"make": brand, "model": model, "constraint": "equal"}
        test_constraints = constraints + [new_constraint]

        db_results = query_carapi_by_constraints(test_constraints, limit=1, unique_models=False)
        if db_results:
            filtered.append(result)

    return filtered

def handle_query(query: str, state: ConversationState):

    
    # create a conversation between user and LLM
    # that will get as many info for DB cars as possible
    state = make_conversation(query, state)

    # If conversation is not finished → return early
    if state.status == "NOT READY":
        return state, []


    # Step 3: Retrieve FAISS context based on user query and LLM responses, and filter them based on constraints
    constraints = state.query_parsed
    retrieved_results = retrieve_candidates(state.queries, state.llm_responses, state.db_cars, k=10)


    filtered_results = filter_retrived_results_by_constraints(retrieved_results, constraints)

    merged_car_results = merge_database_cars_with_retrieval_results(state.db_cars, filtered_results)

    conversation_text = create_conversation_text(state.queries, state.llm_responses)
    prompt = generate_prompt(conversation_text, merged_car_results, filtered_results)

    response = generate_response(prompt)

    state.llm_responses.append(response)

    return state, merged_car_results


def handle_query_raw_llm(query: str):
    prompt = generate_raw_prompt(query)
    response = generate_response(prompt)
    return {
        "recommendations": [],
        "response": response,
    }
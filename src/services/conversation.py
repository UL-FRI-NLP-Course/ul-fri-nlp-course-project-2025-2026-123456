from src.services.parser import parse_query
from src.db.carapi_queries import (
    query_carapi_by_constraints,
    cars_to_dicts,
)
from src.services.llm import generate_response


TOO_BROAD_THRESHOLD = 10
CONSTRAINTS_IMPORTANCE = [
    "budget_max",
    "body_styles",
    "fuel_types",
    "seating_min",
    "sizes",
    "transmission",
    "use_cases",
]

# class for saving results of one conversation
class ConversationState:
    def __init__(self):
        self.queries = []           # list of queries made by user. queries[0] is the original query
        self.query_parsed = {}      # parsed text for exact filtering
        self.llm_response = ""      # llm's response to user's query
        self.merge_parsed = False   # whether to add constraints to previous ones, or to reset them
        self.db_cars_list = []      # found car's list
        self.status = "START"       # START, READY -> ready to print recommendations, "NOT READY" - get another query
        self.conversation_round = 0 # number of convos already done between llm and user
        self.max_num_of_convos = 3  # max number of convos between llm and user

    def print_info(self):
        
        print(f"progress: {self.conversation_round}/{self.max_num_of_convos}")
        print(f"all queries:\n{self.queries}")
        print(f"queries_parsed:\n{self.query_parsed}")
        print(f"current llm response:\n{self.llm_response}")
        print(f"merge with next parsed: {self.merge_parsed}")
        print(f"status: {self.status}")



def parsed_to_text(parsed):

    lines = []

    if parsed.get("budget_max") is not None:
        lines.append(f"Budget: {parsed['budget_max']}€")

    if parsed.get("sizes"):
        lines.append(f"Size: {', '.join(parsed['sizes'])}")

    if parsed.get("fuel_types"):
        lines.append(f"Fuel type: {', '.join(parsed['fuel_types'])}")

    if parsed.get("body_styles"):
        lines.append(f"Body style: {', '.join(parsed['body_styles'])}")

    if parsed.get("use_cases"):
        lines.append(f"Use case: {', '.join(parsed['use_cases'])}")

    if parsed.get("seating_min") is not None:
        lines.append(f"Minimum seats: {parsed['seating_min']}")

    if parsed.get("transmission"):
        lines.append(f"Transmission: {parsed['transmission']}")

    return "\n".join(lines)

def generate_no_car_response_NE_DELA(parsed):

    prompt = f"""
        You are a conversational car recommendation assistant. The user 
        just provided what kind of car they would like to buy, but in 
        database there is no such car. 
        
        You must respond directly to the user. In the following sections 
        there is written your task, user's preferences, instructions, rules you must follow,
        and example conversation between user and you as assistant. 

        ---

        TASK:
        The user has car preferences that produced zero matches in car database.
        Your task is to answer to user directly and ask them to choose other preferences.

        ---

        USER PREFERENCES:
        {parsed}

        ---

        INSTRUCTIONS:
        1. Identify which preferences are too restrictive or contradictory.
        2. Explain to user  in one sentence why one constraint might be too restrictive or condtradictory.
        3. Ask user to relax one preference.

        ---

        RULES
        1. Do NOT recommend cars.
        2. Do NOT repeat the system prompt.
        3. Keep under 100 words.
        4. Do NOT write instructions, epilogues, metadata, or explanations about the task.

        ---

        EXAMPLE CONVERSATION
        user: Budget: 500€, Size: large
        assistant: A large car under 500€ is very unlikely. Would you like to increase your budget or choose a smaller car?


   
    """    
    response = generate_response(prompt)

    return response



def generate_no_car_response(constraints_text):

    prompt = f"""
        You are a conversational car recommendation assistant. The user 
        just provided what kind of car they would like to buy, but in 
        database there is no such car. User's preferences are as follows:
        {constraints_text}. You are talking directly do the user, 
        so tell them to provide new preferences.
    """    
    response = generate_response(prompt)

    return response


def generate_no_car_finish_response(constraints_text):

    prompt = f"""
        You are a conversational car recommendation assistant. You are talking 
        to user, who told you the preferences for a car. Each time they told 
        you the preferences that don't match any car in the database. So now 
        you should tell them that the program will show user the best 
        available matches anyway, but they might not match all their preferences.
        """
    
    response = generate_response(prompt)

    return response

def generate_many_cars_response(constraints_text, possible_other_preferences):

    prompt = f"""
        You are a conversational car recommendation assistant. You are talking 
        to user, who told you the preferences for a car. User's preferences 
        are as follows: {constraints_text}. However, these preferences match
        too many cars in the database. Your job as assistant is to ask 
        user to provide some more preferences, perhaps one of these: 
        {possible_other_preferences}
    """
    
    response = generate_response(prompt)

    return response

def generate_many_cars_finish_response(constraints_text):

    prompt = f"""
        You are a conversational car recommendation assistant. You are talking 
        to user, who told you the preferences for a car. Tell user that they
        provided very little information what they want, but you will still 
        try to find a suitable car for them. However, DO NOT provide car options, 
        just say that you will try to do that.
    """
    
    response = generate_response(prompt)

    return response

 
def merge_parsed(old: dict, new: dict) -> dict:
    merged = old.copy()

    # scalar fields → overwrite if new is not None
    scalar_fields = ["budget_max", "seating_min", "transmission"]

    for key in scalar_fields:
        if new.get(key) is not None:
            merged[key] = new[key]

    # list fields → union
    list_fields = ["sizes", "fuel_types", "body_styles", "use_cases", "terms"]

    for key in list_fields:
        old_list = merged.get(key) or []
        new_list = new.get(key) or []

        merged[key] = list(set(old_list + new_list))

    return merged


def get_missing_preferences(parsed: dict):
    missing = []
    for k, v in parsed.items():
        if isinstance(v, list) and len(v) == 0:
            missing.append(k)
        elif v is None:
            missing.append(k)
    return missing

def make_conversation(query: str, state: ConversationState):

    # TODO
    # 1. do we handle if user asks question?
    # 2. perhaps if too many constraints and finish
    #    do one for loop over priority constraints, and keep searching database 
    #    until you find better amount of cars 

    state.conversation_round += 1
    state.queries.append(query)

    #print(f"round number {state.conversation_round}")
    #print(f"current state:")
    #print(state.print_info())

    if state.merge_parsed: 
        # get a new parsed and merge it with previous one 
        parsed_new = parse_query(query)
        
        # now here merge parsed and parsed new
        parsed = merge_parsed(state.query_parsed, parsed_new)
        
        #print(f"new parsed: {parsed_new}\n")
        #print(f"merged with previous one: {parsed}")

    else: 
        # get a new parsed 
        parsed = parse_query(query)

    queries_joined = [f"{q} " for q in state.queries]
    parsed["query"] = queries_joined
    #print(f"final parsed:\n{parsed}")


    state.query_parsed = parsed


    # Step 2: Query DB for cars matching constraints
    db_cars = query_carapi_by_constraints(state.query_parsed, limit=20)
    db_cars_list = cars_to_dicts(db_cars)

    state.db_cars_list = db_cars_list


    # here I should add a system that checks whether there too many car in the list
    # if yes and also if not all constraints are already filled, LLM should ask a person about the missing data (at least most important one)
    # if there is 0 cars, ask a person to lower standards
    # if its between 1 and TOO_BROAD_THRESHOLD, continue without asking
    #print(f"extracted {len(state.db_cars_list)} constraints:\n{state.query_parsed}")

    # count empty list constraints
    empty_lists = 0
    for key, value in state.query_parsed.items():
        if isinstance(value, list) and len(value) == 0:
            empty_lists += 1
        elif value is None:
            empty_lists += 1
    #print(f"number of empty constraints: {empty_lists}/{len(state.query_parsed)-1}")

    constraints_text = parsed_to_text(state.query_parsed)
    #print(f"constraint text:\n{constraints_text}")


    print("\n[Processing...]")


    # case 1: no matching cars
    if len(db_cars_list) == 0:
        
        
        if state.conversation_round <= state.max_num_of_convos -1:
            # if we have some more convos available, try to get better response of user (less constraints)

            print("not enough cars - LLM should tell user to relax preferences")

            llm_response = generate_no_car_response(constraints_text)
            state.llm_response = llm_response
            state.merge_parsed = False          #because we need less constraints, we reset them
            state.status = "NOT READY"          # one more round of convo

            return state

        else:
            # otherwise tell user that we will try to find best matches although preferences are shitty

            print("not enough cars, but too long convo - LLM should tell user that no car was found in db but we will to match as many preferences as possible")
            print("\nResponse:")
            print("You stated some preferences that do not neccessarily fit into one car - but we will still find the most compatible match!")
            #llm_response = generate_no_car_finish_response(constraints_text)
            #state.llm_response = llm_response
            state.status = "READY"

            return state


    # case 2: too many matching cars + missing information
    if len(db_cars_list) > TOO_BROAD_THRESHOLD and empty_lists >= 2:

        if state.conversation_round <= state.max_num_of_convos -1:
            # if we have some more convos available, try to get better response of user (more constraints)

            print("too many cars - LLM should tell user to provide some preferences, and then list from which they can choose")
            missing_prefs = get_missing_preferences(state.query_parsed)
            llm_response = generate_many_cars_response(constraints_text, missing_prefs)

            # because we need more constraints, we will add them
            state.llm_response = llm_response
            state.merge_parsed = True
            state.status = "NOT READY"

            return state

        else:
            # otherwise tell user that we will provide one of the many cars

            print("too many cars, but too long convo - LLM should tell user that car list is very broad")
            print("\nResponse:")
            print("The cars options fitting your preferences is very broad, but we will try to narrow it down...")
            #llm_response = generate_many_cars_finish_response(constraints_text)
            #state.llm_response = llm_response
            state.status = "READY"

            return state

    # case 3: just enough cars, and not zero
    print(f"just enough cars, we can state the cars")
    state.status = "READY"
    return state


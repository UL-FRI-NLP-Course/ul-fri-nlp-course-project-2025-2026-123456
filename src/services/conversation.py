from src.services.parser import parse_query
from src.db.carapi_queries import (
    query_carapi_by_constraints,
    cars_to_dicts,
)
from src.services.llm import generate_response
import math


TOO_BROAD_THRESHOLD = 10    # yet to set
IMPORTANT_CONSTRAINTS = [
    "make",
    "model",
    "body_type",
    "fuel_type",
    "seats",
    "horsepower_hp",
    "drive_type",
    "transmission",
    "combined_l_per_100km",
    "msrp",
    "doors",
    "range_electric_km",
    "cargo_capacity",
    "ground_clearance_cm",
    "max_towing_capacity_kg",
]

# class for saving results of one conversation
class ConversationState:
    def __init__(self):
        self.queries = []                       # list of queries made by user. queries[0] is the original query
        self.query_parsed = {}                  # parsed text for exact filtering
        self.llm_response = ""                  # llm's response to user's query
        self.merge_parsed = False               # whether to add constraints to previous ones, or to reset them
        self.db_cars_list = []                  # found car's list
        self.status = "START"                   # START, READY -> ready to print recommendations, "NOT READY" - get another query
        self.conversation_round = 0             # number of convos already done between llm and user
        self.max_num_of_convos = 5              # max number of convos between llm and user
        self.empty_constraints = []             # when user specified some important things but not with values
        self.last_prompt_was_question = False   # if the last prompt was question, we should do additional prompt that joins q+a into one query
        self.single_turn = False                # True if wanted without conversation

    def print_info(self):
        
        print(f"progress: {self.conversation_round}/{self.max_num_of_convos}")
        print(f"all queries:\n{self.queries}")
        print(f"queries_parsed:\n{self.query_parsed}")
        print(f"current llm response:\n{self.llm_response}")
        print(f"merge with next parsed: {self.merge_parsed}")
        print(f"status: {self.status}")
        print(f"current unanswered constraints: {self.empty_constraints}")



def parsed_to_text(parsed):

    parts = []

    for item in parsed:
        name = item["name"]
        value = item["value"]
        constraint = item.get("constraint")

        # Check if value is numeric
        try:
            float(value)
            is_numeric = True
        except (TypeError, ValueError):
            is_numeric = False

        if is_numeric and constraint:
            parts.append(f"{name}: {constraint} {value}")
        else:
            parts.append(f"{name}: {value}")

    return ", ".join(parts)



def generate_no_car_response(constraints_text):

    prompt = f"""
        You are a conversational car recommendation assistant. You are talking directly 
        to the user, who just told you the preferences for their new car:
        body_type:
        {constraints_text}. 

        However, in database there is no such car. Explain to them briefly why 
        their combination of preferences might have caused that, and then tell 
        them to provide new preferences.
        
        Do NOT write anything besides that. 
        Do NOT greet them.
        You MUST respond in natural language only.
        Do NOT output code, functions, JSON, or pseudocode.
    """
    
    response = generate_response(prompt)

    return response



def generate_many_cars_response(constraints_text, possible_other_preferences):

    prompt = f"""
        You are a conversational car recommendation assistant. You are talking directly 
        to the user, who just told you the preferences for their new car:
        {constraints_text}. 

        However, these preferences match too many cars in the database. Your task is to suggest 
        user to provide some more preferences, perhaps one of these:
        {possible_other_preferences}.
        Suggest them at least two of the stated, whatever seems important or relevant 
        to what user already stated. You can also come up with some other preference. 
        
        Do NOT write anything besides that. 
        Do NOT greet them.
        You MUST respond in natural language only.
        Do NOT output code, functions, JSON, or pseudocode.
    """
    
    response = generate_response(prompt)

    return response



def generate_missing_constraints_response(missing_constraints):

    constraints_str = ", ".join(missing_constraints)


    prompt = f"""
        You are a conversational car recommendation assistant. You are talking directly 
        to the user, who mentioned a few things that are important to them but didn't specify
        technicalities (for example, they mentioned they want low consumption but didn't tell 
        the number). These things are: {constraints_str}. 

        Your task is to ask them if they can clarify these missing details. 
        
        Do NOT write anything besides that. 
        Do NOT greet them. Start directly with the questions.
        You MUST respond in natural language only.
        Do NOT output code, functions, JSON, or pseudocode.

    """

    #print("PROMPT")
    #print(prompt)

    response = generate_response(prompt)

    return response



def join_response_answer(questions, answers):

    prompt = f"""

        You are a system that receives one or multiple questions, and some of 
        all of their answers. Your task is to form full sentences from answers.
        
        For example:
        Questions: How many seats do you want? Would you like a red car?
        Answers: 5 and yes.
        Your output: I would like 5 seats and a red car.

        Questions you received:
        {questions}
        Answers you received:
        {answers}

        Now write this combined sentences.

        Do NOT write anything besides that.
        You MUST respond in natural language only.
        Do NOT output code, functions, JSON, or pseudocode.

    """
    #print("PROMPT")
    #print(prompt)

    response = generate_response(prompt)

    return response

 
def merge_parsed(old: dict, new: dict) -> dict:
    # Create lookup table from old entries
    merged = {item["name"]: item.copy() for item in old}

    # Update or insert new entries
    merged = {item["name"]: item.copy() for item in old}

    for item in new:
        name = item["name"]

        # If value is None -> remove existing entry
        # ^ tole je mal sus ampak ideja je, da ce dobimo v nov query za item, k je ze notr v parsu, to loh pomen dve stvari
        # al smo lihkar vprasal po tej stvari in SPET ni blo jasnga odgovora 
        # al pa je User rekel, da v bistvu noce tega constrainta vec (kar probably resulta v None)
        if item.get("value") is None:
            merged.pop(name, None)
            continue

        # Otherwise update/add
        merged[name] = item.copy()

    return list(merged.values())




def get_missing_preferences(parsed, possible_prefs):
    lookup = {item["name"]: item.get("value") for item in parsed}

    missing = []

    for field in possible_prefs:
        if field not in lookup or lookup[field] is None:
            missing.append(field)

    return missing



def do_we_finish(round, parsed, alpha=0.40):

    # must have at least 2 turns
    if round < 2:
        return False

    all_fields = 43     # hardcoded from carapi_schema.py
    filled_fields = sum(
        1 for item in parsed
        if item.get("value") is not None
    )
    coverage = filled_fields / all_fields

    # decay over time + coverage penalty
    p_continue = (1 - coverage) * math.exp(-alpha * (round - 2))

    return p_continue < 0.25

def make_conversation(query: str, state: ConversationState):

    """
    Function that creates conversation with user (when state.single_turn == False).

    Parses query
    |
    Creates a few-shot conversation with user:
    asks for 'None's in query / asks for more preferences / asks to relax constraints
    | 
    Returns final list of cars (from SQL table)
    """


    state.conversation_round += 1
    state.queries.append(query)


    # first check whether previous llm response was question -> we need to join the queries
    if state.last_prompt_was_question == True:

        new_query = join_response_answer(state.llm_response, state.queries[-1])
        state.queries[-1] = new_query
        state.last_prompt_was_question = False


    # merge preferences
    if not state.merge_parsed:
        # ce je to prvi krog pol sam sparsamo
        parsed = parse_query(query, state.conversation_round)
        state.merge_parsed = True   # in zdej tega ne spreminjam vec 
    else: 
        # otherwise we need to merge all preferences
        parsed_new = parse_query(state.queries[-1], state.conversation_round)
        parsed = merge_parsed(state.query_parsed, parsed_new)

    state.query_parsed = parsed




    # Step 2: Query DB for cars matching constraints
    db_cars = query_carapi_by_constraints(state.query_parsed, limit=20)
    db_cars_list = cars_to_dicts(db_cars)

    state.db_cars_list = db_cars_list


    # check if there are any preferences that LLM didn't catch a value of
    empty_important_constraints = []
    for item in state.query_parsed:

        val = item.get("value")
        con = item.get("constraint")

        # set default constraint 
        if val is not None and con is None:
            state.query_parsed[item][con] = "equal"

        if val is None:
            empty_important_constraints.append(item.get("name"))


    # reset the constraints
    # (also could keep a track on those that LLM already asked about)
    state.empty_constraints = empty_important_constraints

    # if it's a single turn, then we leave after first parsing
    if state.single_turn:
        print("SINGLE TURN CONVO - leaving make conversation")
        state.status = "READY"
        return state


    # check if this was the last convo of LLM and user and then return if yes
    fin = do_we_finish(state.conversation_round, state.query_parsed)

    if fin:
        print("CONVO WAS ALREADY TOO LONG BYE")
        state.status = "READY"

        return state



    #print("\n[Processing Convo...]")


    # ROUND 1 OF QUESTIONING: LLM should ask about empty constraiants 
    if len(state.empty_constraints) > 0:

        print(f"LLM should ask user about the empty preferences: {state.empty_constraints}")
        llm_response = generate_missing_constraints_response(state.empty_constraints)

        state.llm_response = llm_response
        state.last_prompt_was_question = True # so that we parse llm response plus answer
        #state.merge_parsed = True
        state.status = "NOT READY"          # one more round of convo

        return state


    # ROUND 2 OF QUESTIONING: LLM should ask to add preferences or to relax them


    # get a nicer form for LLM prompt 
    constraints_text = parsed_to_text(state.query_parsed)


    # case 1: no matching cars
    if len(db_cars_list) == 0:
        
        # try to get better response of user (less constraints)
        print("not enough cars - LLM should tell user to relax preferences")

        llm_response = generate_no_car_response(constraints_text)
        state.llm_response = llm_response
        #state.merge_parsed = False          #because we need less constraints, we reset them
        state.status = "NOT READY"          # one more round of convo

        return state

    # case 2: too many matching cars
    if len(db_cars_list) > TOO_BROAD_THRESHOLD:

        # try to get better response of user (more constraints)
        print("too many cars - LLM should tell user to provide some preferences, and then list from which they can choose")

        # get missing preferences
        missing_prefs_list = get_missing_preferences(state.query_parsed, IMPORTANT_CONSTRAINTS)

        if missing_prefs_list:

            # if its not empty
            missing_prefs = ", ".join(missing_prefs_list)
            llm_response = generate_many_cars_response(constraints_text, missing_prefs)
            state.llm_response = llm_response
            #state.merge_parsed = True
            state.status = "NOT READY"

            return state


    # case 3: just enough cars, and not zero
    print(f"just enough cars, we can state the cars")
    state.status = "READY"
    return state



if __name__ == '__main__':

    sample = [
        {'name': 'body_type', 'value': 'SUV', 'constraint': 'equal'},
        {'name': 'seats', 'value': None, 'constraint': 'min'},
        {'name': 'fuel_type', 'value': 'electric', 'constraint': 'equal'},
        {'name': 'combined_l_per_100km', 'value': None, 'constraint': None},
    ]

    important_fields = [
        "make",
        "model",
        "body_type",
        "fuel_type",
        "seats",
        "horsepower_hp",
        "drive_type",
        "transmission",
        "combined_l_per_100km",
        "msrp",
    ]

    print(get_missing_preferences(sample, important_fields))
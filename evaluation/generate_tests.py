import sys
import os
import argparse
import json
from contextlib import contextmanager

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.db.carapi_queries import query_carapi_by_constraints, query_unique_models_by_constraints


def get_query_constraint_pairs():

    pairs = []

    query = "I am looking for a car from BMW or Mercedes with at least 7 seats"

    constraint = [{'name': 'make', 'value': ['BMW', 'Mercedes'], 'constraint': 'equal'},
                  {'name': 'seats', 'value': 7, 'constraint': 'min'}]

    cars = query_unique_models_by_constraints(constraint)
    pairs.append((query, constraint))

    query = "I am looking for a Mazda that costs at most 15000 euro"

    constraint = [{'name': 'make', 'value': "Mazda", 'constraint': 'equal'},
                  {'name': 'msrp', 'value': 15000, 'constraint': 'max'}]

    cars = query_unique_models_by_constraints(constraint)
    pairs.append((query, constraint))

    query = "I am looking for a coupe from 2015 or newer"

    constraint = [{'name': 'body_type', 'value': 'coupe', 'constraint': 'equal'},
                  {'name': 'year', 'value': 2015, 'constraint': 'min'}]

    cars = query_unique_models_by_constraints(constraint)
    pairs.append((query, constraint))

    query = "I am looking for an SUV with manual transmission"

    constraint = [{'name': 'body_type', 'value': 'SUV', 'constraint': 'equal'},
                  {'name': 'transmission', 'value': 'manual', 'constraint': 'equal'}]

    cars = query_unique_models_by_constraints(constraint)
    pairs.append((query, constraint))

    query = "I am looking for an SUV from Mazda with a maximum of 5 seats"

    constraint = [{'name': 'make', 'value': "Mazda", 'constraint': 'equal'},
                  {'name': 'body_type', 'value': 'SUV', 'constraint': 'equal'},
                  {'name': 'seats', 'value': 5, 'constraint': 'max'}]

    cars = query_unique_models_by_constraints(constraint)
    pairs.append((query, constraint))

    query = "I am looking for a diesel powered, 7 seater SUV with a 50 liter fuel tank"

    constraint = [{'name': 'engine_type', 'value': "diesel", 'constraint': 'equal'},
                  {'name': 'body_type', 'value': 'SUV', 'constraint': 'equal'},
                  {'name': 'seats', 'value': 7, 'constraint': 'min'},
                  {'name': 'fuel_tank_capacity', 'value': 50, 'constraint': 'min'}]

    cars = query_unique_models_by_constraints(constraint)
    pairs.append((query, constraint))

    # for car in cars:
    #     print(car)

    return pairs


def generate_test():

    output_path = "evaluation/eval_tests.jsonl"

    f = open(output_path, "w")

    pairs = get_query_constraint_pairs()

    for pair in pairs:

        query = pair[0]
        constraint = pair[1]

        cars = query_unique_models_by_constraints(constraint)

        all_cars = []
        for car in cars:
            brand = car.get("brand", "Unknown")
            model = car.get("model", "")
            all_cars.append(f"{brand} {model}".strip())

        print(cars)

        row = {
            "question": query,
            "expected_answer": all_cars,
            "constraints": constraint,
            "expected_docs": []
        }

        f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    # get_query_constraint_pairs()
    generate_test()

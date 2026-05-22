import sys
import os
import argparse
import json
from contextlib import contextmanager

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.db.carapi_queries import query_carapi_by_constraints, query_unique_models_by_constraints
from test_db_queries import get_car_data


def main():

    test_file = "evaluation/eval_tests.jsonl"
    result_file = "evaluation/eval_results.jsonl"

    constraint_file = "evaluation/constraint_results.jsonl"

    f_test = open(test_file, "r")
    f_result = open(result_file, "r")

    f_constraint = open(constraint_file, "w")

    for line_test, line_result in zip(f_test, f_result):
        # print(line_test)
        # print("--")
        # print(line_result)
        #
        # print("-----------")

        line_test = json.loads(line_test)
        line_result = json.loads(line_result)

        expected = line_test.get("expected_answer", "")
        constraints = line_test.get("constraints", "")
        predicted = line_result.get("predicted", "")

        for predicted_car in predicted:
            # print("predicted car " + predicted_car)
            # print("expected car " + str(expected))
            if predicted_car not in expected:

                all_con = []
                all_val = []
                all_wanted = []
                for constraint in constraints:
                    con = constraint.get("name")
                    val = constraint.get("value")
                    wanted = constraint.get("constraint")

                    all_con.append(con)
                    all_val.append(val)
                    all_wanted.append(wanted)


                car_dict_predicted = get_car_data(predicted_car.split() , all_con)
                f_constraint.write("Dejanski podatki: " + str(car_dict_predicted) + "\n")
                f_constraint.write("Zahteve: " + str(constraints) + "\n")
                f_constraint.write("\n")


    # car_dict = get_car_data(["Ford", "Edge"], ["seats", "cargo_capacity", "model"])
    # print(car_dict)


if __name__ == "__main__":
    main()

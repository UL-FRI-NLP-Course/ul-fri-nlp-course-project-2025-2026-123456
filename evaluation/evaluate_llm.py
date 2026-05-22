import sys
import os
import argparse
import json
from contextlib import contextmanager

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.services.rag_service import handle_query, handle_query_raw_llm
from src.config import FAISS_INDEX_PATH
from src.db.database import init_db
# from src.services.llm import init_llm
from src.main import init_rag
from src.ingestion.embedder import init_embedder
from src.services.conversation import ConversationState


@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

def evaluate(raw_llm=False, with_ollama=False):
    if not with_ollama:
        from src.services.llm import init_llm
        init_llm()

    if raw_llm:
        print()
        # print("Running in raw LLM mode (no RAG context or database recommendations)")
    else:
        init_rag()

    state = ConversationState()
    state.single_turn = True

    input_path = "evaluation/eval_tests.jsonl"
    output_path = "evaluation/eval_results.jsonl"

    # print("Conversational Recommender System for Vehicles")
    # print("Type 'exit' or 'quit' to stop.\n")

    total = 0
    correct_top1 = 0
    correct_top3 = 0

    with open(input_path, "r") as f:

        f_result = open(output_path, "w")

        for line in f:

            line = json.loads(line)
            question = line["question"]
            expected = line["expected_answer"]

            print(question)
            print(expected)

            top_answers = []

            try:
                # query = input("You: ").strip()
                query = question
                if query.lower() in ("exit", "quit"):
                    # print("\nGoodbye!")
                    break

                if not query:
                    continue

                # print("\n[Processing...]")
                if raw_llm:
                    with suppress_stdout():
                        response = handle_query_raw_llm(query)
                else:
                    with suppress_stdout():
                        state = ConversationState()
                        state.single_turn = True
                        state, response = handle_query(query, state)

                # print("\nResponse:")
                # print(result.get("response", "No response generated"))

                # top_answers = []

                print(state.status)

                if state.status == "READY":
                    # print("\nTop Recommendations:")
                    for i, rec in enumerate(response, 1):
                        brand = rec.get("brand", "Unknown")
                        model = rec.get("model", "")
                        # print(f"  {i}. {brand} {model}\n")
                        top_answers.append(f"{brand} {model}".strip())

                print("Predicted:", top_answers)

                total += 1

                expected_set = {
                    x.lower().strip()
                    for x in expected
                }

                predicted_set = {
                    x.lower().strip()
                    for x in top_answers
                }

                # if len(predicted_set) > 0:
                #     if expected_set == predicted_set[0]:
                #         correct_top1 += 1
                #
                # if expected_set in predicted_set:
                #     correct_top3 += 1

                # expected_set = set(expected)
                # predicted_set = set(top_answers)

                intersection = expected_set & predicted_set

                correct = len(intersection)
                extra = len(predicted_set - expected_set)
                missed = len(expected_set - predicted_set)

                precision = correct / len(predicted_set) if predicted_set else 0
                recall = correct / len(expected_set) if expected_set else 0

                f1 = (
                    2 * precision * recall / (precision + recall)
                    if (precision + recall) > 0
                    else 0
                )

                result_row = {
                    "question": question,
                    "expected": expected,
                    "predicted": top_answers,
                    # "top1_correct": (
                    #         len(predicted_set) > 0
                    #         and expected_set == predicted_set[0]
                    # ),
                    "top3_correct": (
                            expected_set in predicted_set
                    ),
                    "intersection": list(intersection),
                    "correct_count": correct,
                    "extra_count": extra,
                    "missed_count": missed,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                }

                f_result.write(json.dumps(result_row) + "\n")

            except KeyboardInterrupt:
                # print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                # print(f"Error: {e}")
                import traceback
                traceback.print_exc()

    print("\n========================")
    print("Evaluation Complete")
    print("========================")

    if total > 0:
        print(f"Samples: {total}")
        print(f"Top-1 Accuracy: {correct_top1 / total:.2%}")
        print(f"Top-3 Accuracy: {correct_top3 / total:.2%}")

    summary = {
        "summary": {
            "samples": total,
            "top1_accuracy": correct_top1 / total if total > 0 else 0,
            "top3_accuracy": correct_top3 / total if total > 0 else 0,
        }
    }

    # f_result.write(json.dumps(summary) + "\n")

    f_result.close()

if __name__ == "__main__":
    evaluate()
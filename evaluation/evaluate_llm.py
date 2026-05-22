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

def evaluate(raw_llm=False, with_cpu=True):
    if not with_cpu:
        from src.services.llm import init_llm
        init_llm()

    if raw_llm:
        print()
        # print("Running in raw LLM mode (no RAG context or database recommendations)")
    else:
        init_rag()

    state = ConversationState()

    # print("Conversational Recommender System for Vehicles")
    # print("Type 'exit' or 'quit' to stop.\n")

    with open("evaluation/eval_dataset.jsonl", "r") as f:

        f_result = open("evaluation/eval_results.jsonl", "w")

        for line in f:

            line = json.loads(line)
            question = line["question"]
            expected = line["expected_answer"]

            print(question)
            print(expected)

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
                        top_cars = handle_query_raw_llm(query)
                else:
                    with suppress_stdout():
                        state, top_cars = handle_query(query, state)

                # print("\nResponse:")
                # print(result.get("response", "No response generated"))

                top_answers = []

                print(state.status)

                if state.status == "READY":
                    # print("\nTop Recommendations:")
                    for i, rec in enumerate(top_cars[:3], 1):
                        brand = rec.get("brand", "Unknown")
                        model = rec.get("model", "")
                        # print(f"  {i}. {brand} {model}\n")
                        top_answers.append(str(brand) + " " + str(model))

            except KeyboardInterrupt:
                # print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                # print(f"Error: {e}")
                import traceback
                traceback.print_exc()

            f_result.write(json.dumps(question))
            f_result.write(json.dumps(expected))
            f_result.write(json.dumps(top_answers) + "\n")

            print(top_cars)

    f_result.close()

if __name__ == "__main__":
    evaluate()
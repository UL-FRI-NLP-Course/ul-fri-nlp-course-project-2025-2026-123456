import sys
import os
import argparse
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.services.rag_service import handle_query, handle_query_raw_llm
from src.config import FAISS_INDEX_PATH
from src.db.database import init_db
# from src.services.llm import init_llm
from src.main import init_rag
from src.ingestion.embedder import init_embedder


def evaluate(raw_llm=False):
    # init_llm()

    if raw_llm:
        print("Running in raw LLM mode (no RAG context or database recommendations)")
    else:
        init_rag()

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
                    print("\nGoodbye!")
                    break

                if not query:
                    continue

                print("\n[Processing...]")
                if raw_llm:
                    result = handle_query_raw_llm(query)
                else:
                    result = handle_query(query)

                print("\nResponse:")
                print(result.get("response", "No response generated"))

                top_answers = []

                if not raw_llm:
                    print("\nTop Recommendations:")
                    for i, rec in enumerate(result.get("recommendations", [])[:3], 1):
                        brand = rec.get("brand", "Unknown")
                        model = rec.get("model", "")
                        print(f"  {i}. {brand} {model}\n")
                        top_answers.append(str(brand) + " " + str(model))

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()

            f_result.write(json.dumps(question))
            f_result.write(json.dumps(expected))
            f_result.write(json.dumps(top_answers) + "\n")

            print(result.get("recommendations", [])[:3], 1)

    f_result.close()

if __name__ == "__main__":
    evaluate()
import sys
import os
import argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.services.rag_service import handle_query, handle_query_raw_llm
from src.config import FAISS_INDEX_PATH
from src.db.database import init_db
from src.services.llm import init_llm


def main():
    parser = argparse.ArgumentParser(description="Vehicle recommender chat")
    parser.add_argument(
        "--raw-llm",
        action="store_true",
        help="Use baseline LLM mode without RAG context or database recommendations",
    )
    args = parser.parse_args()

    init_llm()
    if not args.raw_llm:
        if not os.path.exists(FAISS_INDEX_PATH):
            print("ERROR: FAISS index not found.")
            print("Run ingestion first: python3 scripts/ingest_pdfs.py")
            sys.exit(1)

        try:
            init_db()
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")

    print("Conversational Recommender System for Vehicles")
    if args.raw_llm:
        print("Mode: RAW LLM (no RAG, no DB)")
    else:
        print(f"FAISS index: {FAISS_INDEX_PATH}")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            query = input("You: ").strip()
            if query.lower() in ("exit", "quit"):
                print("\nGoodbye!")
                break

            if not query:
                continue

            print("\n[Processing...]")
            if args.raw_llm:
                result = handle_query_raw_llm(query)
            else:
                result = handle_query(query)

            print("\nResponse:")
            print(result.get("response", "No response generated"))

            if not args.raw_llm:
                print("\nTop Recommendations:")
                for i, rec in enumerate(result.get("recommendations", [])[:3], 1):
                    brand = rec.get("brand", "Unknown")
                    model = rec.get("model", "")
                    print(f"  {i}. {brand} {model}\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

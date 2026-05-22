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
from src.ingestion.embedder import init_embedder

from src.services.conversation import ConversationState

def init_rag():
    if not os.path.exists(FAISS_INDEX_PATH):
        print("ERROR: FAISS index not found.")
        print("Run ingestion first: python3 scripts/ingest_pdfs.py")
        return 
     
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")

    init_embedder()

def main(raw_llm=False):
    init_llm()

    if raw_llm:
        print("Running in raw LLM mode (no RAG context or database recommendations)")
    else:
        init_rag()

    print("Conversational Recommender System for Vehicles")
    print("Type 'exit' or 'quit' to stop.\n")

    state = ConversationState()

    while True:
        try:
            query = input("You: ").strip()
            if query.lower() in ("exit", "quit"):
                print("\nGoodbye!")
                break

            if not query:
                continue

            print("\n[Processing...]")
            if raw_llm:
                result = handle_query_raw_llm(query)

                print("\nResponse:")
                print(result.get("response", "No response generated"))

            else:
                # LLM + RAG
                state, car_recommendations = handle_query(query, state)

                print("\nResponse:")
                print(state.llm_responses[-1])

                # check whether already we print reommendations 
                # or did we ask user to provide additional info
                if state.status == "READY":
                    print("\nTop Recommendations:")
                    for i, rec in enumerate(car_recommendations[:10], 1):
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

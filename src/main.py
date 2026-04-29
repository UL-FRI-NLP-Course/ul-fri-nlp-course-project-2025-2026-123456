import sys
import os

# Add project root to path for script execution
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.services.rag_service import handle_query
from src.config import FAISS_INDEX_PATH, CARS_CSV_PATH
from src.db.database import init_db
from scripts.load_cars import load_cars_from_csv


def main():
    if not os.path.exists(FAISS_INDEX_PATH):
        print("ERROR: FAISS index not found.")
        print(f"Run ingestion first: python3 scripts/ingest_pdfs.py")
        sys.exit(1)

    # Initialize DB and load sample data if needed
    try:
        init_db()
        load_cars_from_csv(CARS_CSV_PATH)
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")

    print("Conversational Recommender System for Vehicles")
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
            result = handle_query(query)

            print("\nResponse:")
            print(result.get("response", "No response generated"))
            
            print("\nTop Recommendations:")
            for i, rec in enumerate(result.get("recommendations", [])[:3], 1):
                brand = rec.get("brand", "Unknown")
                model = rec.get("model", "")
                price_min = rec.get("price_min", 0)
                price_max = rec.get("price_max", 0)
                fuel = rec.get("fuel_type", "N/A")
                body = rec.get("body_type", "N/A")
                score = rec.get("score", 0.0)
                print(
                    f"  {i}. {brand} {model}\n"
                    f"     Price: €{price_min:,.0f} - €{price_max:,.0f} | "
                    f"Fuel: {fuel} | Type: {body}\n"
                    f"     Score: {score:.3f} "
                    f"(constraint: {rec.get('constraint_score', 0):.2f}, "
                    f"semantic: {rec.get('faiss_score', 0):.2f})\n"
                )

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

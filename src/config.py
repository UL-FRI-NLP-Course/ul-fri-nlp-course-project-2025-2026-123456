import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("./.env")

# Database
DB_URL = os.getenv("DATABASE_URL")

# Embeddings and RAG
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
COLUMN_EMBEDDING_THRESHOLD = float(os.getenv("COLUMN_EMBEDDING_THRESHOLD", "0.40"))
COLUMN_EXTRACTION_LIMIT = int(os.getenv("COLUMN_EXTRACTION_LIMIT", "5"))

HF_LLM_MODEL = os.getenv("HF_LLM_MODEL", "Qwen/Qwen2.5-14B-Instruct")
HF_LLM_PARSING_MODEL = os.getenv("HF_LLM_PARSING_MODEL", "Qwen/Qwen2.5-14B-Instruct")
USE_4BIT_QUANTIZATION = os.getenv("USE_4BIT_QUANTIZATION", "true").lower() == "true"

BASE_DIR = Path(__file__).resolve().parent.parent

# Paths for FAISS index and metadata (one-time ingestion output)
DATA_DIR = str(BASE_DIR / "data")
VECTOR_STORE_DIR = str(Path(DATA_DIR) / "vector_store")
FAISS_INDEX_PATH = str(Path(VECTOR_STORE_DIR) / "index.faiss")
METADATA_PATH = str(Path(VECTOR_STORE_DIR) / "metadata.json")
PDF_ROOT = str(Path(DATA_DIR) / "pdfs")
CARS_CSV_PATH = str(Path(DATA_DIR) / "cars.csv")

# Paths for CarAPI stats column embeddings
CARAPI_COLUMN_EMBEDDINGS_FILE = str(Path(DATA_DIR) / "carapi_column_embeddings.npy")

CARAPI_BASEURL = "https://carapi.app"
CARAPI_TOKEN = os.getenv("CARAPI_TOKEN")
CARAPI_SECRET = os.getenv("CARAPI_SECRET")
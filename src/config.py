import os
from dotenv import load_dotenv

load_dotenv("./.env")

# Database
DB_URL = os.getenv("DATABASE_URL")

# Embeddings and RAG
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "all-MiniLM-L6-v2"
)
HF_LLM_MODEL = os.getenv("HF_LLM_MODEL", "Qwen/Qwen2-7B-Instruct")

# Paths for FAISS index and metadata (one-time ingestion output)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
VECTOR_STORE_DIR = os.path.join(DATA_DIR, "vector_store")
FAISS_INDEX_PATH = os.path.join(VECTOR_STORE_DIR, "index.faiss")
METADATA_PATH = os.path.join(VECTOR_STORE_DIR, "metadata.json")
PDF_ROOT = os.path.join(DATA_DIR, "pdfs")
CARS_CSV_PATH = os.path.join(DATA_DIR, "cars.csv")

# LLM settings for 8-bit quantization (for Llama-2-7b on 4080)
USE_8BIT_QUANTIZATION = os.getenv("USE_8BIT_QUANTIZATION", "true").lower() == "true"
LLM_DEVICE_MAP = "auto"  # auto device map for multi-GPU or mixed precision

CARAPI_BASEURL = "https://carapi.app"
CARAPI_TOKEN = os.getenv("CARAPI_TOKEN")
CARAPI_SECRET = os.getenv("CARAPI_SECRET")
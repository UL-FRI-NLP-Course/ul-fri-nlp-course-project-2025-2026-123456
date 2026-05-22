# Natural language processing course: `Conversational Recommender System for Vehicles`

This is a conversational vehicle recommendation system for users who want practical car suggestions from natural-language queries. It combines structured filtering over a CarAPI-based SQLite database (for hard constraints such as budget, body type, seats, and fuel) with semantic brochure retrieval from a FAISS index, then uses an LLM to produce concise, grounded recommendations.

### Run RAG Query Loop
```bash
python src/main.py
```

Then type queries like:
```
You: I am looking for a sporty coupe that wont break the bank
```

And the system responds:
```
Response:
 Let me know if you need any clarification or have additional questions.

Summary: For a sporty coupe that won't break the bank, the Ford Mustang, Toyota 86, and Mazda MX-5 are top recommendations. The Mustang offers a powerful engine and modern styling, while the Toyota 86 provides a fun-to-drive experience with excellent handling. The Mazda MX-5 stands out for its lightweight design, aggressive performance, and iconic status among enthusiasts. All three vehicles deliver on the promise of a sporty coupe without a hefty price tag.

Tradeoffs include different levels of luxury features, fuel efficiency, and overall size. The Mustang may be slightly larger but offers more interior space and luxury features compared to the compact Toyota 86 and the smaller Mazda MX-5. The Mazda MX-5 sacrifices some comfort and cargo space for its lightweight, agile nature, making it ideal for enthusiasts seeking a true sports car

Top Recommendations:
  1. Ford Mustang

  2. Toyota 86

  3. Mazda MX-5
```

The system will:
1. Embed your query
2. Retrieve top-K chunks from FAISS
3. Parse the query for keywords and specifications
4. Fetch relevant vehicles from the database
3. Rank candidates
4. Generate a recommendation with LLM

### Architecture

The system has two information sources:

1. **FAISS Vector Store** (from PDF brochures)
   - Semantic similarity search
   - Returns context snippets for LLM
   - Scores based on embedding similarity

2. **SQLite Structured Database** (from CarAPI)
   - Hard constraints filtering (budget, fuel type, body style, seats, transmission)
   - Car specifications (price, horsepower, safety rating, dimensions, etc.)
   - Fast exact-match queries

### Project Structure

```
src/
├── main.py                   # RAG pipeline entry point
├── config.py                 # Configuration + paths
├── ingestion/
│   ├── chunker.py            # Text chunking
│   ├── embedder.py           # SentenceTransformers embeddings
│   └── faiss_store.py        # FAISS utilities
├── services/
│   ├── rag_service.py        # RAG orchestration
│   ├── retrival.py           # FAISS retrieval
│   ├── llm.py                # Llama-2-7b generation
│   ├── ranking.py            # Candidate ranking
│   └── parser.py             # Query parsing
└── db/
    ├── database.py           # Structured DB connection
    ├── carapi_schema.py      # Data schemas
    └── carapi_queries.py     # Data querying


scripts/
├── get_carapi_stats.py       # Download car stats from CarAPI
├── get_pdf_data.py           # Download pdf brochures
├── ingest_carapi_stats.py    # One-time carapi stats ingestion
└── ingest_pdfs.py            # One-time pdf ingestion

data/
├── carapi/                   # CarAPI stats
├── pdfs/                     # Pdf brochures
└── vector_store/             # FAISS index + metadata
```

### Installation

```bash
# Clone and install
git clone ul-fri-nlp-course-project-2025-2026-123456
cd ul-fri-nlp-course-project-2025-2026-123456

# install dependencies (virtual environment recommended)
pip install -r requirements.txt
```

### Configuration

Edit `.env` to override defaults:
```
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
HF_LLM_MODEL=meta-llama/Llama-2-7b-chat-hf
USE_8BIT_QUANTIZATION=true
DATABASE_URL=... 
```

### Setup Steps (one-time)

#### 1. Prepare PDF Brochures
Download car brochures and place them in:
```
data/pdfs/
├── audi/
│   └── A4_brochure.pdf
├── mazda/
│   └── CX-5_brochure.pdf
└── ...
```

Use the provided `get_pdf_data.py` script to download sample brochures:
```bash
python scripts/get_pdf_data.py download
```

#### 2. Run Ingestion
This extracts PDFs, chunks, embeds, and builds the FAISS index:
```bash
python scripts/ingest_pdfs.py
```

Output:
- `data/vector_store/index.faiss` - FAISS index
- `data/vector_store/metadata.json` - Chunk metadata

#### 3. Prepare structured data

Download car stats from the [CarAPI](https://carapi.app/) website.

You must provide `CARAPI_TOKEN` and `CARAPI_SECRET` to `.env` file. 

```bash
python scripts/get_carapi_stats.py
```

Output:
- Downloads raw json data to `data/carapi/`

#### 4. Run Ingestion for structured DB
This creates the `carapi.db` SQLite database. 

```bash
python scripts/ingest_carapi_stats.py
```

### Benchmark

To benchmark the system, we support multiple inference modes that allow comparison between the same LLM under different levels of retrieval and interaction.


#### 1. Raw LLM (no RAG, no database access)

This mode runs the same LLM with the same persona and instructions as the main pipeline, but without retrieval augmentation or database-based recommendations.

```bash
python src/main.py --raw-llm
```

#### 2. Single-turn LLM

This mode runs the same system as the main pipeline, but as a non-conversational
setup. It does not ask any additional question, but directly return car recommendations.

```bash
python src/main.py --single-turn
```

# Natural language processing course: `Conversational Recommender System for Vehicles`

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

Use the provided `get_data.py` script to download sample brochures:
```bash
python scripts/get_data.py
```

#### 2. Run Ingestion
This extracts PDFs, chunks, embeds, and builds the FAISS index:
```bash
python scripts/ingest_pdfs.py
```

Output:
- `data/vector_store/index.faiss` - FAISS index
- `data/vector_store/metadata.json` - Chunk metadata

#### 3. Initialize Database & Load Sample Data

```bash
python3 scripts/load_cars.py
```

Output:
- Creates `data/cars.db` (SQLite)
- Loads cars from `data/cars.csv`

### Run RAG Query Loop
```bash
python src/main.py
```

Then type queries like:
```
You: I need a fuel-efficient family car with good safety ratings
```

The system will:
1. Embed your query
2. Retrieve top-K chunks from FAISS
3. Rank candidates
4. Generate a recommendation from Llama-2-7b-chat

### Project Structure

```
src/
├── main.py                   # RAG pipeline entry point
├── config.py                 # Configuration + paths
├── ingestion/
│   ├── pdf_loader.py         # PDF extraction (PyMuPDF)
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
    ├── database.py           # Future DB connection
    ├── models.py             # Data models
    └── queries.py            # Data querying


scripts/
├── add_cars_to_db.py         # Programmatically add cars to DB
├── get_data.py               # Download pdf brochures
├── ingest_pdfs.py            # One-time ingestion
└── load_cars.py              # Load car data from CSV to DB

data/
├── pdfs/                     # Pdf brochures
└── vector_store/             # FAISS index + metadata
```

### Architecture

The system has two information sources:

1. **FAISS Vector Store** (from PDF brochures)
   - Semantic similarity search
   - Returns context snippets for LLM
   - Scores based on embedding similarity

2. **SQLite Structured Database** (from CSV)
   - Hard constraints filtering (budget, fuel type, body style, seats, transmission)
   - Car specifications (price, horsepower, safety rating, dimensions, etc.)
   - Fast exact-match queries

### Database Schema

**Table: `cars`**

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| brand | String | Car manufacturer (e.g., "Audi") |
| model | String | Model name (e.g., "A4") |
| price_min | Float | Minimum price (€) |
| price_max | Float | Maximum price (€) |
| fuel_type | String | "petrol", "diesel", "hybrid", "electric" |
| body_type | String | "sedan", "suv", "hatchback", "wagon", "coupe" |
| seats | Integer | Number of seats |
| transmission | String | "manual", "automatic" |
| horsepower | Integer | Engine power (hp) |
| torque | Integer | Engine torque (Nm) |
| fuel_consumption | Float | L/100km (0 for electric) |
| co2_emissions | Float | g/km |
| width, length, height | Float | Dimensions (mm) |
| weight | Integer | Curb weight (kg) |
| trunk_volume | Integer | Trunk/cargo space (L) |
| has_awd | Boolean | All-wheel drive available |
| safety_rating | Float | Euro NCAP rating (0-5) |
| year | Integer | Model year |

# Natural language processing course: `Conversational Recommender System for Vehicles`

This is a conversational vehicle recommendation system for users who want practical car suggestions from natural-language queries. It combines structured filtering over a CarAPI-based SQLite database (for hard constraints such as budget, body type, seats, and fuel) with semantic brochure retrieval from a FAISS index, then uses an LLM to produce concise, grounded recommendations.

### Run RAG Query Loop
```bash
python src/main.py
```

Then type queries like:
```
You: I am looking for an affordable family SUV with 7 seats.
```

The system might ask you for aditional information:
```
Response:
To help narrow down your options, could you please specify if you prefer a particular make or model? Additionally, do you have any requirements regarding the fuel type or the seating arrangement like second-row captain's chairs versus a bench seat?
```

```
You: I do not have a brand or model preference, but I would like to have a diesel engine.
```

Before generating the final response.

```
Given your preference for a diesel engine and need for a 7-seater SUV, I recommend focusing on the Audi Q7, Chevrolet Suburban, and Chevrolet Tahoe. These models balance affordability and实用性建议如下：

1. **Audi Q7**: Offers robust performance and luxurious interiors suitable for a family. However, note that finding a diesel variant might be limited due to market availability, typically preferring gasoline engines. 

2. **Chevrolet Suburban**: Provides ample space and reliable diesel option, ideal for large families needing extra room. It's known for durability and comfort, making long journeys easier.

3. **Chevrolet Tahoe**: Another strong contender offering a comfortable ride and sufficient seating capacity. Like the Suburban, it has a diesel version which ensures good fuel efficiency and lower running costs over time.

While the Mercedes-Benz models offer premium features, they tend to be more expensive and less common in diesel versions. The Land Rover Discovery is also a great choice, though it primarily uses petrol engines and is priced higher than the others mentioned here.

For your specific needs, the **Suburban** and **Tahoe** stand out due to their reliability, spaciousness, and availability of diesel engines, balancing practicality and cost-effectiveness well.

Top Recommendations:
  1. Audi Q7

  2. Land Rover Discovery

  3. Mercedes-Benz GL-Class

  4. Mercedes-Benz GLS-Class

  5. Chevrolet Suburban

  6. Chevrolet Tahoe
```

The system will:
1. Embed your query
2. Retrieve top-K chunks from FAISS
3. Parse the query with LLM to extract constraints
4. Fetch relevant vehicles from the database
5. Generate a recommendation with LLM

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
├── main.py                            # RAG pipeline entry point
├── config.py                          # Configuration + paths
├── ingestion/
│   ├── chunker.py                     # Text chunking
│   ├── embedder.py                    # SentenceTransformers embeddings
│   └── faiss_store.py                 # FAISS utilities
├── services/
│   ├── rag_service.py                 # RAG orchestration
│   ├── retrival.py                    # FAISS retrieval
│   ├── llm.py                         # LLM generation
│   ├── conversation.py                # Conversation logic
│   └── parser.py                      # Query parsing
└── db/
    ├── database.py                    # Structured DB connection
    ├── carapi_schema.py               # Data schema and metadata
    ├── carapi_queries.py              # Data querying
    └── carapi_column_emb.py           # Embedding utilities


scripts/
├── get_carapi_stats.py                # Download car stats from CarAPI
├── get_pdf_data.py                    # Download pdf brochures
├── ingest_carapi_stats.py             # One-time carapi stats ingestion
└── ingest_pdfs.py                     # One-time pdf ingestion

data/
├── carapi/                            # CarAPI stats
├── pdfs/                              # Pdf brochures
└── vector_store/                      # FAISS index + metadata

benchmark/
├── benchmark_embedder.py              # Benchmark for embedding models
├── queries_with_labeled_scores.json   # Labeled data for benchmark
└── show_column_embeddings.py          # Utils for testing embedding models

evaluation/
├── evaluate_llm.py                    # Evaluation of the CRS
└── generate_tests.pt                  # Generate tests for the evaluation
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

Edit `.env` to override defaults defined in `src/config.py`.

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
This creates the `carapi.db` SQLite database and generates the embeddings for the attributes. 

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

#### Attribute embedding benchmark

Benchmark different embedding models on the task of embedding CarAPI attributes.

```bash
python benchmark/benchmark_embedder.py
```

### Evaluation 

To evaluate the performance of CRS first generate tests.

```bash
python evaluation/generate_tests.py
```

Then run the benchmark. 

```bash
python evaluation/evaluate_llm.py

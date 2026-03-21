# PolicyRAG

RAG system for SEC financial filing QA with hallucination scoring, citation extraction, and LLM provider switching.

## Motivation

Financial analysts and compliance teams need trustworthy answers from SEC filings, but LLMs hallucinate. PolicyRAG addresses this by combining retrieval-augmented generation with multi-dimensional evaluation — faithfulness scoring via NLI, citation verification, and context relevance metrics — to provide transparent, auditable QA in regulated environments.

<!-- TODO: Add chat UI screenshot -->

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        React Frontend                            │
│  ┌──────────┐  ┌───────────────────┐  ┌──────────────────────┐  │
│  │ Sidebar   │  │  Chat Interface   │  │   Source Panel       │  │
│  │ Documents │  │  Query + Answer   │  │   Cited Chunks       │  │
│  │ Upload    │  │  Trust Scores     │  │   Relevance Bars     │  │
│  └──────────┘  └───────────────────┘  └──────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼─────────────────────────────────────┐
│                      FastAPI Backend                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Ingestion   │  │  RAG Pipeline │  │  Evaluation Engine    │  │
│  │  PDF→Chunks  │  │  Retrieve →   │  │  Faithfulness (NLI)   │  │
│  │  SEC Split   │  │  Context →    │  │  Citation Metrics     │  │
│  │  Embed       │  │  Generate →   │  │  Relevance Scoring    │  │
│  │              │  │  Cite          │  │  Completeness (LLM)   │  │
│  └──────┬──────┘  └──────┬───────┘  └────────────────────────┘  │
│         │                │                                       │
│  ┌──────▼──────┐  ┌──────▼───────┐  ┌────────────────────────┐  │
│  │  ChromaDB   │  │ LLM Factory  │  │  PostgreSQL            │  │
│  │  Vectors    │  │ OpenAI/Ollama│  │  Documents, Evals      │  │
│  └─────────────┘  └──────────────┘  └────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Features

- **SEC Filing Ingestion** — Upload PDFs or fetch directly from EDGAR by ticker
- **Section-Aware Chunking** — Regex-based SEC section detection (Items 1, 1A, 7, 8, etc.)
- **Cited Answers** — LLM responses with [N] citation markers linked to source chunks
- **Hallucination Scoring** — NLI-based faithfulness evaluation using DeBERTa
- **Citation Metrics** — Precision (entailment check) and recall (coverage)
- **LLM Switching** — Hot-swap between OpenAI and Ollama models per query
- **Cross-Encoder Re-ranking** — ms-marco for improved retrieval quality
- **Redis Caching** — Deterministic cache keys, TTL-based, invalidation on re-ingestion
- **Evaluation Dashboard** — Historical scores, provider comparison, analytics

<!-- TODO: Add evaluation dashboard screenshot -->

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| API | FastAPI, Pydantic, SSE |
| Vector DB | ChromaDB (cosine similarity) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Re-ranker | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| NLI Model | cross-encoder/nli-deberta-v3-base |
| LLM | OpenAI API / Ollama (local) |
| Database | PostgreSQL 16 (async SQLAlchemy) |
| Cache | Redis 7 |
| Orchestration | Docker Compose |

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your OpenAI key (optional — works with Ollama only)

# 2. Start all services
docker-compose up -d

# 3. Pull an Ollama model (if not using OpenAI)
docker exec -it policyrag-ollama-1 ollama pull llama3.1

# 4. Open the UI
open http://localhost:3000

# 5. API docs
open http://localhost:8080/docs
```

## API Reference

### Query
```
POST /api/v1/query
{
  "query": "What was Apple's total revenue in 2023?",
  "document_ids": [],
  "provider": "ollama",
  "model": "llama3.1"
}
```

### Documents
```
POST /api/v1/documents          # Upload PDF
POST /api/v1/documents/edgar    # Fetch from EDGAR
GET  /api/v1/documents          # List all
GET  /api/v1/documents/{id}     # Get detail
DELETE /api/v1/documents/{id}   # Delete
```

### Models
```
GET  /api/v1/models             # List available
GET  /api/v1/models/active      # Current model
POST /api/v1/models/switch?provider=openai&model=gpt-4o-mini
```

### Evaluation
```
GET /api/v1/evaluation/history   # Paginated history
GET /api/v1/evaluation/analytics # Aggregate scores
GET /api/v1/evaluation/compare   # Provider comparison
```

## Evaluation Methodology

| Metric | Method | Range |
|--------|--------|-------|
| Faithfulness | LLM claim decomposition → NLI entailment check | 0-1 |
| Hallucination Score | 1 - Faithfulness | 0-1 |
| Citation Precision | NLI check: cited sentence entailed by source chunk | 0-1 |
| Citation Recall | % of substantive sentences with citations | 0-1 |
| Context Relevance | Avg cosine similarity (query ↔ chunks) | 0-1 |
| Completeness | LLM-as-judge scoring | 0-1 |
| Trust Score | Weighted average (faith 40%, prec 20%, recall 10%, rel 15%, comp 15%) | 0-1 |

## Design Decisions

1. **No full LangChain** — Only `langchain-text-splitters` for chunking. Direct API calls for everything else.
2. **NLI for faithfulness** — Using DeBERTa NLI model instead of LLM-as-judge for factual grounding (faster, more consistent).
3. **Unified ChromaDB collection** — Metadata filtering instead of per-document collections (simpler, supports cross-document queries).
4. **Async everywhere** — SQLAlchemy async, Redis async, httpx for Ollama. ML models run in thread pools.
5. **Models at build time** — Embedding, re-ranker, and NLI models downloaded during Docker build.
6. **Optional OpenAI** — System fully works with Ollama only for air-gapped deployments.

## Development

```bash
# Backend
cd backend
pip install -e ".[dev]"
pytest tests/

# Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
policyrag/
├── docker-compose.yaml
├── sql/init.sql
├── backend/
│   ├── policyrag/
│   │   ├── api/routes/          # FastAPI endpoints
│   │   ├── core/                # RAG pipeline, retriever, citations
│   │   ├── db/                  # SQLAlchemy models, repositories
│   │   ├── evaluation/          # Faithfulness, citation metrics
│   │   ├── ingestion/           # PDF parsing, SEC splitting, EDGAR
│   │   ├── llm/                 # Provider abstraction (OpenAI/Ollama)
│   │   ├── cache/               # Redis query cache
│   │   └── schemas/             # Pydantic models
│   └── tests/
└── frontend/
    └── src/
        ├── components/          # React UI components
        ├── hooks/               # Custom React hooks
        ├── services/            # API client
        └── types/               # TypeScript interfaces
```

## Future Enhancements

- **Conformal Prediction** — Calibrated confidence intervals for trust scores using conformal prediction sets
- **Streaming Responses** — Token-level SSE streaming with incremental citation highlighting
- **Multi-Turn Conversations** — Context-aware follow-up queries with conversation memory
- **Fine-Tuned Embeddings** — Domain-adapted embedding model trained on SEC filings for improved retrieval

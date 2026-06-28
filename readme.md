# ZenESG Regulatory Radar — Feature 5

AI-powered daily ESG regulatory news intelligence system.

---

## One-line mental model

```
Fetch ESG news → parse it → store it → index in ChromaDB → RAG-rank it → show in Daily Radar
```

---

## What it does

- Monitors 20+ global ESG news sources daily — automatically
- Extracts ESG keywords dynamically from a PDF — zero hardcoding
- Parses articles into structured regulatory records using Groq
- Indexes parsed updates in ChromaDB for semantic ranking
- Shows top ranked ESG updates in the Daily Radar dashboard
- Includes Tavily web intelligence for supplementary regulatory signals

---

## Daily News Architecture

```
sustainability_keywords.pdf
          |
          v
  keyword_extractor.py
          |
          v
RSS feeds → data_ingestion.py → esg_radar.db (articles)
                                      |
                                      v
                                  parser.py
                                      |
                                      v
                              esg_radar.db (parsed_articles)
                                      |
                                      v
                               rag_pipeline.py
                                      |
                                      v
                                  chroma_db/
                                      |
                                      v
                                  radar.py
                                      |
                                      v
                         dashboard.py → Daily Radar tab

Tavily path:
keywords.pdf → tavily_collector.py → esg_radar.db (tavily_articles) → rag_pipeline.py → chroma_db/
```

---

## File Map

| File | What it does |
|------|-------------|
| `scheduler.py` | Automates the daily pipeline sequence — ingestion, parsing, Tavily, RAG |
| `dashboard.py` | Main Streamlit app entry point |
| `radar.py` | Daily Radar UI — top ESG updates and details |
| `data_ingestion.py` | Fetches RSS feeds, filters by ESG keywords, saves raw articles |
| `parser.py` | Sends articles to Groq, extracts structured regulatory fields |
| `tavily_collector.py` | Collects regulatory web intelligence via Tavily |
| `keyword_extractor.py` | Reads sustainability PDF, extracts ESG keywords dynamically |
| `rag_pipeline.py` | Loads parsed articles into ChromaDB and ranks them |
| `console_utils.py` | Console utilities for Windows output handling |
| `config.py` | Settings and paths — RSS feeds, DB path, PDF path, Chroma path |
| `db_schema.py` | Creates all SQLite tables on fresh setup |
| `esg_radar.db` | Main SQLite database for articles and parsed updates |
| `chroma_db/` | ChromaDB vector index used by RAG pipeline |
| `sustainability_keywords.pdf` | ESG keyword source for filtering and extraction |
| `Dockerfile` | Docker image definition |
| `docker-compose.yml` | Docker run configuration |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template — copy to `.env` |

---

## Setup

### 1. Create `.env`

```bash
copy .env.example .env
```

Add your keys:

```
GROQ_API_KEY=...
TAVILY_API_KEY=...
OPENAI_API_KEY=...
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Run — only one command needed!

```bash
python scheduler.py
```

This will automatically:
- Run data ingestion — fetch fresh ESG news
- Run parser — structure articles with Groq
- Run Tavily collector — fetch web intelligence
- Run RAG pipeline — index into ChromaDB
- Repeat every day at 8:00 AM automatically

To start the dashboard separately:

```bash
streamlit run dashboard.py
```

---

## Run with Docker

```bash
docker compose up --build
```

Open: `http://localhost:8501`

---

## Dashboard

The current Streamlit app renders a single Daily Radar page showing top ranked ESG regulatory updates.

| Page | What it shows |
|------|--------------|
| Daily Radar | Top ranked ESG updates with expandable article details |

---

## Database Tables

| Table | What it stores |
|-------|---------------|
| `articles` | Raw RSS articles |
| `parsed_articles` | Structured regulatory data — regulation, jurisdiction, impact, action |
| `tavily_articles` | Web intelligence — full content, relevance score |
| `fetch_logs` | RSS fetch history |
| `impact_assessments` | Saved company compliance reports |

---

## Common Issues

| Problem | Fix |
|---------|-----|
| No Daily Radar data | Check esg_radar.db and chroma_db/ exist |
| RAG results stale | Rerun python rag_pipeline.py |
| no such table error | Run python db_schema.py |
| Docker shows empty data | Confirm esg_radar.db and chroma_db/ in project root |
| Groq or Tavily errors | Check .env keys |

---

## What to commit

```
All source code files
Dockerfile + docker-compose.yml
requirements.txt
.env.example
esg_radar.db
chroma_db/
sustainability_keywords.pdf
README.md

NOT: .env, venv/, __pycache__/
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data ingestion | Python, feedparser, requests |
| Web intelligence | Tavily API |
| Keyword extraction | pymupdf — dynamic, zero hardcoding |
| AI parsing | Groq LLaMA 3.3 70B |
| Vector search | ChromaDB + sentence-transformers |
| Database | SQLite |
| Dashboard | Streamlit |

---

## Accuracy

System achieves 8.5 to 9 out of 10 on regulatory queries:

| Company type | Correctly identified |
|-------------|---------------------|
| UK investment firms | TCFD, FCA, ESRS |
| India companies | BRSR, SEBI |
| EU companies | ESRS, CSRD, CBAM |
| Singapore | ISSB, SGX mandates |
| Shipping EU | ESRS, IMO regulations |

---

Built as Feature 5 — Regulatory Radar — of the ZenESG platform.
# ZenESG Radar - Teammate Working Guide

Main product goal:

```text
Show ESG/regulatory daily news reliably.
```

Company assessment and chat are secondary. If RAG-ranked Daily Radar works, the core
project is useful.

## 1. What The App Does

ZenESG Radar collects ESG news, stores it in SQLite, parses important updates with
Groq, indexes structured data in ChromaDB, and shows everything in Streamlit.

Main app entry:

```text
dashboard.py
```

Main daily news UI:

```text
radar.py
```

## 2. RAG Daily News Is The Priority

If you only debug one thing, debug this flow:

```text
RSS feeds -> SQLite DB -> Groq parsing -> ChromaDB/RAG -> Daily Radar UI
```

Daily Radar does not fetch live RSS directly. It uses ChromaDB for RAG ranking, then
uses SQLite to load full source details for display.

## 3. Critical Daily News Files

`config.py` - RSS feeds, database path, Chroma path, keyword PDF path.

`sustainability_keywords.pdf` - keyword source for ESG relevance.

`keyword_extractor.py` - extracts keywords from the PDF.

`data_ingestion.py` - fetches RSS feeds and saves matched news into `articles`.

`parser.py` - parses RSS articles with Groq and saves into `parsed_articles`.

`tavily_collector.py` - fetches extra web intelligence into `tavily_articles`.

`radar.py` - renders the Daily Radar tab from RAG-ranked ChromaDB results.

`rag_pipeline.py` - loads RSS/Tavily data into ChromaDB and ranks Daily Radar items.

`dashboard.py` - main Streamlit app and tab layout.

`db_schema.py` - creates required tables on fresh/Docker setup.

## 4. Daily News Flow

```text
config.py RSS_FEEDS
  -> keyword_extractor.py reads sustainability_keywords.pdf
  -> data_ingestion.py
  -> esg_radar.db / articles
  -> parser.py
  -> esg_radar.db / parsed_articles
  -> rag_pipeline.py
  -> chroma_db/
  -> radar.py
  -> dashboard.py / Daily Radar tab
```

Tavily flow:

```text
sustainability_keywords.pdf
  -> tavily_collector.py
  -> esg_radar.db / tavily_articles
  -> rag_pipeline.py
  -> chroma_db/
  -> radar.py / Latest Web Intelligence
```

## 5. Important Database Files

`esg_radar.db` is the main SQLite database. It is required if the teammate should
see existing saved news immediately.

Important tables:

`articles` - raw RSS articles saved by `data_ingestion.py`.

`parsed_articles` - structured regulation records saved by `parser.py`.

`tavily_articles` - Tavily web results saved by `tavily_collector.py`.

`fetch_logs` - RSS fetch history for debugging.

`impact_assessments` - saved company assessment reports.

## 6. ChromaDB

`chroma_db/` is the local vector index used by Daily Radar RAG ranking, company
matching, and ESG chat context.

For the teammate to get the same existing search results, the repo must include:

```text
esg_radar.db
chroma_db/
```

Without these, the app can run, but existing regulations will be missing until the
pipeline is run again.

## 7. Project Structure

```text
zenESG-radar/
  dashboard.py              Main Streamlit app
  radar.py                  Daily Radar / top news UI
  data_ingestion.py         RSS ingestion
  parser.py                 Groq article parser
  tavily_collector.py       Tavily web intelligence collector
  keyword_extractor.py      Extracts ESG keywords from PDF
  sustainability_keywords.pdf
  config.py                 Feeds, DB paths, Chroma paths
  db_schema.py              Creates SQLite tables
  rag_pipeline.py           Chroma loading and regulation search
  qa_rag.py                 ESG chat agent
  impact_assesment.py       CLI impact assessment
  esg_radar.db              Main SQLite DB
  chroma_db/                Chroma vector index
  Dockerfile                Docker image config
  docker-compose.yml        Docker run config
  requirements.txt          Python dependencies
  .env.example              Env template
  .env                      Local secrets, do not commit
  .dockerignore             Docker build exclusions
  .gitignore                Git exclusions
```

## 8. Environment Variables

Create `.env` from `.env.example`:

```powershell
copy .env.example .env
```

Required:

```text
GROQ_API_KEY=...
TAVILY_API_KEY=...
```

Never commit `.env`.

## 9. Run With Docker

Recommended for teammates:

```powershell
docker compose up --build
```

Open:

```text
http://localhost:8501
```

Current Docker mounts:

```text
./esg_radar.db -> /app/esg_radar.db
./chroma_db    -> /app/chroma_db
```

So `esg_radar.db` and `chroma_db/` must exist in the project root.

## 10. Run Without Docker

```powershell
pip install -r requirements.txt
streamlit run dashboard.py
```

## 11. Build Fresh Data

Run in order:

```powershell
python data_ingestion.py
python parser.py
python tavily_collector.py
python rag_pipeline.py
streamlit run dashboard.py
```

Docker version:

```powershell
docker compose run --rm zenesg-radar python data_ingestion.py
docker compose run --rm zenesg-radar python parser.py
docker compose run --rm zenesg-radar python tavily_collector.py
docker compose run --rm zenesg-radar python rag_pipeline.py
```

## 12. Main Screens

Company Assessment: `dashboard.py -> render_company_assessment()`

Latest Regulations: `dashboard.py -> render_latest_regulations()`

Database Stats: `dashboard.py -> render_database_stats()`

ESG Chat: `dashboard.py + qa_rag.py`

Daily Radar: `dashboard.py -> radar.py -> rag_pipeline.py -> ChromaDB`

## 13. Common Issues

No Daily Radar data: check `esg_radar.db`, `parsed_articles`, and `chroma_db/`.

`no such table: parsed_articles`: run latest code with `db_schema.py`, then restart
Docker/app.

Docker runs but no existing regulations: make sure `esg_radar.db` and `chroma_db/`
exist in the project root.

Groq or Tavily errors: check `.env` keys.

RAG-ranked news returns nothing: check `chroma_db/` or rerun `rag_pipeline.py`.

RSS fetch gives no articles: check `RSS_FEEDS` and `sustainability_keywords.pdf`.

## 14. What To Commit

Commit:

```text
source code, Dockerfile, docker-compose.yml, requirements.txt, .env.example,
esg_radar.db, chroma_db/, PROJECT_WORKING_GUIDE.md
```

Do not commit:

```text
.env, venv/, __pycache__/, .streamlit/secrets.toml
```

## 15. Mental Model

Daily news:

```text
Fetch into SQLite -> parse into SQLite -> index in ChromaDB -> RAG rank -> display
```

RAG:

```text
SQLite parsed data -> ChromaDB -> company search/chat context
```

Docker:

```text
If Docker cannot see esg_radar.db and chroma_db/, it cannot show existing data.
```

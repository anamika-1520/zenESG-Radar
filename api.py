from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE = "esg_radar.db"

app = FastAPI(title="ZenESG Regulatory Radar API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def root():
    return {"app": "ZenESG Regulatory Radar", "status": "running"}


@app.get("/api/daily-radar")
def daily_radar(
    region: str = Query(default="Global"),
    impact: str = Query(default="All"),
    limit: int = Query(default=10, ge=1, le=25),
):
    # ---------- RAG-ranked news ----------
    try:
        from rag_pipeline import find_daily_news_candidates

        rag_results = []
        for candidate in find_daily_news_candidates(region, impact, limit):
            conn = get_db()
            row = conn.execute(
                """
                SELECT
                    p.regulation_name, p.jurisdiction, p.impact_level,
                    p.change_type, p.action_required, p.summary,
                    p.regulator, p.deadline, p.affected_sectors,
                    a.title, a.description, a.source, a.url,
                    a.fetched_at, a.relevance_score
                FROM parsed_articles p
                JOIN articles a ON p.article_id = a.id
                WHERE a.id = ?
                """,
                (candidate["article_id"],),
            ).fetchone()
            conn.close()
            if row:
                item = dict(row)
                item["rag_score"] = candidate["score"]
                rag_results.append(item)
    except Exception as e:
        rag_results = []
        rag_error = str(e)
    else:
        rag_error = None

    # ---------- Tavily news ----------
    try:
        conn = get_db()
        tavily_rows = conn.execute(
            """
            SELECT title, content, source, url, query_used, relevance_score, fetched_at
            FROM tavily_articles
            WHERE relevance_score >= 0.85
            ORDER BY relevance_score DESC, fetched_at DESC
            LIMIT 5
            """
        ).fetchall()
        conn.close()
        tavily_results = [dict(r) for r in tavily_rows]
    except Exception as e:
        tavily_results = []
        tavily_error = str(e)
    else:
        tavily_error = None

    return {
        "generated_at": str(datetime.now()),
        "region": region,
        "impact_filter": impact,
        "rag": {
            "total": len(rag_results),
            "error": rag_error,
            "results": rag_results,
        },
        "tavily": {
            "total": len(tavily_results),
            "error": tavily_error,
            "results": tavily_results,
        },
    }
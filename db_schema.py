import os
import sqlite3
from config import DATABASE, DATABASE_URL, get_db_type

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

def get_connection():
    if get_db_type() == "postgres" and PSYCOPG2_AVAILABLE:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect(DATABASE)

def ensure_database_schema():
    conn = get_connection()
    cursor = conn.cursor()
    
    is_postgres = get_db_type() == "postgres" and PSYCOPG2_AVAILABLE
    pk = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS articles (
            id {pk},
            title TEXT NOT NULL,
            description TEXT,
            url TEXT UNIQUE,
            source TEXT,
            published TEXT,
            matched_keywords TEXT,
            relevance_score INTEGER DEFAULT 0,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS fetch_logs (
            id {pk},
            source_url TEXT,
            total_articles INTEGER,
            relevant_articles INTEGER,
            status TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS parsed_articles (
            id {pk},
            article_id INTEGER UNIQUE,
            regulation_name TEXT,
            jurisdiction TEXT,
            regulator TEXT,
            change_type TEXT,
            affected_sectors TEXT,
            deadline TEXT,
            impact_level TEXT,
            summary TEXT,
            action_required TEXT,
            parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS tavily_articles (
            id {pk},
            title TEXT,
            content TEXT,
            url TEXT UNIQUE,
            source TEXT,
            query_used TEXT,
            relevance_score REAL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS impact_assessments (
            id {pk},
            company_name TEXT,
            company_sector TEXT,
            company_jurisdiction TEXT,
            assessment TEXT,
            regulations_used TEXT,
            assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Schema ready — DB type: {'PostgreSQL' if is_postgres else 'SQLite'}")
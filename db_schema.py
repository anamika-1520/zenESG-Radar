import sqlite3

from config import DATABASE


def ensure_database_schema():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT UNIQUE,
            source TEXT,
            published TEXT,
            matched_keywords TEXT,
            relevance_score INTEGER DEFAULT 0,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fetch_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT,
            total_articles INTEGER,
            relevant_articles INTEGER,
            status TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS parsed_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tavily_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            url TEXT UNIQUE,
            source TEXT,
            query_used TEXT,
            relevance_score REAL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS impact_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            company_sector TEXT,
            company_jurisdiction TEXT,
            assessment TEXT,
            regulations_used TEXT,
            assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()

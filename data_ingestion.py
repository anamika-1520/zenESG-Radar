import feedparser
import re
import json
import socket
from datetime import datetime
from console_utils import configure_utf8_console
from keyword_extractor import extract_keywords_from_pdf
from db_schema import get_connection, ensure_database_schema
from config import (
    RSS_FEEDS,
    FETCH_INTERVAL_HOURS,
    MAX_DESCRIPTION_LENGTH
)

configure_utf8_console()

# Global timeout
socket.setdefaulttimeout(10)

# ============================================
# ARTICLE PROCESSING
# ============================================

def clean_text(text):
    if not text:
        return ""
    text = re.sub('<.*?>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def check_relevance(title, description, keywords):
    text = (title + " " + description).lower()
    matched = []
    for keyword in keywords:
        if keyword.lower() in text:
            matched.append(keyword)
    return matched, len(matched)

def save_article(conn, article):
    cursor = conn.cursor()
    from config import get_db_type
    is_postgres = get_db_type() == "postgres"
    
    try:
        if is_postgres:
            cursor.execute("""
                INSERT INTO articles 
                (title, description, url, source, 
                 published, matched_keywords, relevance_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                article['title'],
                article['description'],
                article['url'],
                article['source'],
                article['published'],
                json.dumps(article['matched_keywords']),
                article['relevance_score']
            ))
        else:
            cursor.execute("""
                INSERT INTO articles 
                (title, description, url, source, 
                 published, matched_keywords, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                article['title'],
                article['description'],
                article['url'],
                article['source'],
                article['published'],
                json.dumps(article['matched_keywords']),
                article['relevance_score']
            ))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False

def log_fetch(conn, source_url, total, relevant, status):
    cursor = conn.cursor()
    from config import get_db_type
    is_postgres = get_db_type() == "postgres"
    
    try:
        if is_postgres:
            cursor.execute("""
                INSERT INTO fetch_logs 
                (source_url, total_articles, relevant_articles, status)
                VALUES (%s, %s, %s, %s)
            """, (source_url, total, relevant, status))
        else:
            cursor.execute("""
                INSERT INTO fetch_logs 
                (source_url, total_articles, relevant_articles, status)
                VALUES (?, ?, ?, ?)
            """, (source_url, total, relevant, status))
        conn.commit()
    except Exception:
        conn.rollback()

# ============================================
# MAIN FETCHER
# ============================================

def fetch_from_feed(feed_url, keywords, conn):
    try:
        socket.setdefaulttimeout(10)
        feed = feedparser.parse(
            feed_url,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        if not feed.entries:
            print(f"  ⚠️ Empty/timeout: {feed_url[:50]}")
            return 0

        source_name = feed.feed.get('title', feed_url)
        total = len(feed.entries)
        relevant_count = 0
        new_count = 0

        for entry in feed.entries:
            title = entry.get('title', '')
            description = clean_text(
                entry.get('description', '') or
                entry.get('summary', '')
            )[:MAX_DESCRIPTION_LENGTH]

            url = entry.get('link', '')
            published = entry.get('published', str(datetime.now()))

            matched_kws, score = check_relevance(title, description, keywords)

            if score > 0:
                relevant_count += 1
                article = {
                    "title": title,
                    "description": description,
                    "url": url,
                    "source": source_name,
                    "published": published,
                    "matched_keywords": matched_kws,
                    "relevance_score": score
                }
                if save_article(conn, article):
                    new_count += 1

        log_fetch(conn, feed_url, total, relevant_count, "success")

        print(f"  ✅ {source_name[:30]}")
        print(f"     Total: {total} | Relevant: {relevant_count} | New: {new_count}")

        return relevant_count

    except Exception as e:
        try:
            log_fetch(conn, feed_url, 0, 0, f"error: {str(e)[:100]}")
        except Exception:
            pass
        print(f"  ❌ Failed: {feed_url[:50]}")
        print(f"     Error: {str(e)[:60]}")
        return 0

# ============================================
# MAIN
# ============================================

def run_ingestion():
    print("\n" + "="*50)
    print("🌍 ZenESG Regulatory Radar")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)

    print("\n📚 Step 1: Loading keywords...")
    keywords = extract_keywords_from_pdf()
    print(f"✅ {len(keywords)} keywords ready!")

    print("\n🗄️  Step 2: Database setup...")
    ensure_database_schema()
    conn = get_connection()
    print("✅ Database ready!")

    print(f"\n📡 Step 3: Fetching from {len(RSS_FEEDS)} feeds...")

    total_relevant = 0
    for feed_url in RSS_FEEDS:
        count = fetch_from_feed(feed_url, keywords, conn)
        total_relevant += count

    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    print(f"✅ Sources checked : {len(RSS_FEEDS)}")
    print(f"✅ ESG articles    : {total_relevant}")

    # Top articles
    from config import get_db_type
    is_postgres = get_db_type() == "postgres"
    cursor = conn.cursor()

    if is_postgres:
        cursor.execute("""
            SELECT title, source, relevance_score, matched_keywords
            FROM articles
            ORDER BY relevance_score DESC, fetched_at DESC
            LIMIT 5
        """)
    else:
        cursor.execute("""
            SELECT title, source, relevance_score, matched_keywords
            FROM articles
            ORDER BY relevance_score DESC, fetched_at DESC
            LIMIT 5
        """)

    rows = cursor.fetchall()
    if rows:
        print("\n🏆 TOP 5 MOST RELEVANT ARTICLES:")
        for i, row in enumerate(rows, 1):
            try:
                kws = json.loads(row[2] if is_postgres else row[3])[:3]
            except Exception:
                kws = []
            print(f"\n{i}. {row[0][:60]}")
            print(f"   Source: {row[1]}")

    conn.close()
    print("\n✅ Ingestion complete!")

if __name__ == "__main__":
    run_ingestion()
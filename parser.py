from groq import AuthenticationError, Groq
import sqlite3
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from console_utils import configure_utf8_console
from config import DATABASE

# Setup
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)
configure_utf8_console()
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


def validate_groq_key():
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing from .env")

    if not GROQ_API_KEY.startswith("gsk_"):
        raise RuntimeError("GROQ_API_KEY does not look like a Groq API key")

# ============================================
# DATABASE
# ============================================

def setup_db():
    conn = sqlite3.connect(DATABASE)
    conn.cursor().execute("""
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
    """)
    conn.commit()
    return conn

# ============================================
# GROQ PARSING
# ============================================

def parse_article(title, description, retries=3):
    """Send article to Groq → get structured ESG data"""

    prompt = f"""You are an ESG regulatory analyst.
Analyze this article and return ONLY a valid JSON object.
No explanation. No markdown. Just pure JSON.

Article Title: {title}
Article Text: {description}

Return this exact JSON structure:
{{
    "regulation_name": "Name of specific regulation if mentioned (e.g. TCFD, CSRD, BRSR). If no specific regulation is named, infer the most relevant framework from context (e.g. 'Paris Agreement', 'UN Climate Framework', 'SFDR', 'EU Taxonomy', 'UNFCCC'). Never return null — always infer something meaningful.",
    "jurisdiction": "e.g. UK, EU, India, Global — infer from article context even if not explicitly stated. Never return null.",
    "regulator": "Specific regulator if mentioned (e.g. FCA, SEC, SEBI). If not mentioned, infer the most likely governing body from context (e.g. 'UNFCCC', 'European Commission', 'UN General Assembly', 'National Government'). Never return null.",
    "change_type": "new_rule or rollback or update or proposal or other",
    "affected_sectors": ["sector1", "sector2"],
    "deadline": "deadline if mentioned or null",
    "impact_level": "high or medium or low",
    "summary": "2 sentence summary of what changed and why it matters",
    "action_required": "what companies should do now in 1 sentence"
}}"""

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an ESG regulatory analyst. Always respond with valid JSON only. Never return null for regulation_name, jurisdiction, or regulator — always infer a meaningful value from context."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )

            text = response.choices[0].message.content.strip()
            text = text.replace("```json", "").replace("```", "").strip()

            return json.loads(text)

        except json.JSONDecodeError:
            print(f"   ⚠️  JSON error — attempt {attempt + 1}")
            time.sleep(2)
            continue

        except AuthenticationError:
            raise

        except Exception as e:
            error = str(e)
            if "429" in error:
                print(f"   ⏳ Rate limit — waiting 30s...")
                time.sleep(30)
                continue
            else:
                print(f"   ❌ Error: {error[:60]}")
                return None

    return None

# ============================================
# MAIN
# ============================================

def run_parser():
    print("\n" + "="*50)
    print("🤖 ZenESG — Groq Article Parser")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)

    try:
        validate_groq_key()
    except RuntimeError as e:
        print(f"\nError: {e}")
        print("Update GROQ_API_KEY in .env, then run parser.py again.")
        return

    conn = setup_db()
    cursor = conn.cursor()

    # Unparsed + null wale dono lo
    cursor.execute("""
        SELECT a.id, a.title, a.description,
               a.source, a.relevance_score
        FROM articles a
        LEFT JOIN parsed_articles p
            ON a.id = p.article_id
        WHERE (
            p.article_id IS NULL
            OR p.regulation_name IS NULL
            OR p.regulator IS NULL
            OR p.jurisdiction IS NULL
        )
        AND a.relevance_score >= 2
        ORDER BY a.relevance_score DESC
    """)

    articles = cursor.fetchall()
    print(f"\n📋 Articles to parse: {len(articles)}")

    if not articles:
        print("✅ Sab articles already parsed!")
        conn.close()
        return

    success = 0
    failed = 0

    for i, (art_id, title, desc, source, score) in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}]")
        print(f"   📰 {title[:55]}...")
        print(f"   Source: {source} | Score: {score}")

        try:
            result = parse_article(title, desc)
        except AuthenticationError:
            print("\nError: Groq rejected GROQ_API_KEY with 401 Unauthorized.")
            print("Create or copy a valid Groq API key into .env, then run parser.py again.")
            break

        if result:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO parsed_articles (
                        article_id, regulation_name,
                        jurisdiction, regulator,
                        change_type, affected_sectors,
                        deadline, impact_level,
                        summary, action_required
                    ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (
                    art_id,
                    result.get("regulation_name") or "General ESG",
                    result.get("jurisdiction") or "Global",
                    result.get("regulator") or "Not specified",
                    result.get("change_type"),
                    json.dumps(result.get("affected_sectors", [])),
                    result.get("deadline"),
                    result.get("impact_level"),
                    result.get("summary"),
                    result.get("action_required")
                ))
                conn.commit()
                success += 1

                print(f"   ✅ Done!")
                print(f"   📌 {result.get('regulation_name')} | "
                      f"🌍 {result.get('jurisdiction')} | "
                      f"⚡ {result.get('impact_level')}")
                print(f"   📋 {result.get('action_required')}")

            except Exception as e:
                print(f"   ❌ Save error: {e}")
                failed += 1
        else:
            failed += 1

        time.sleep(1)

    # Summary
    print("\n" + "="*50)
    print("📊 PARSING SUMMARY")
    print("="*50)
    print(f"✅ Successfully parsed : {success}")
    print(f"❌ Failed              : {failed}")
    print(f"📦 Total processed     : {len(articles)}")

    # High impact dikhao
    cursor.execute("""
        SELECT p.regulation_name, p.jurisdiction,
               p.action_required, a.title
        FROM parsed_articles p
        JOIN articles a ON p.article_id = a.id
        WHERE p.impact_level = 'high'
        ORDER BY p.parsed_at DESC
        LIMIT 5
    """)

    high = cursor.fetchall()
    if high:
        print("\n🔴 HIGH IMPACT REGULATIONS:")
        for row in high:
            print(f"\n  📌 {row[0]} | 🌍 {row[1]}")
            print(f"  📋 {row[2]}")
            print(f"  📰 {row[3][:50]}...")

    conn.close()
    print("\n✅ Parsing complete!")

if __name__ == "__main__":
    run_parser()

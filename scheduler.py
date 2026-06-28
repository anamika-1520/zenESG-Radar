import schedule
import time
import subprocess
from datetime import datetime

def run_pipeline():
    print(f"\n{'='*50}")
    print(f"Daily ESG Pipeline — {datetime.now()}")
    print('='*50)

    steps = [
        ("Data Ingestion", "data_ingestion.py"),
        ("Parser",         "parser.py"),
        ("Tavily",         "tavily_collector.py"),
        ("RAG Pipeline",   "rag_pipeline.py"),
    ]

    for name, script in steps:
        print(f"\n▶ Running {name}...")
        result = subprocess.run(
            ["python", script],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {name} done!")
        else:
            print(f"❌ {name} failed: {result.stderr[:100]}")

    print("\n✅ Daily pipeline complete!")
    print("Dashboard will show fresh news now!")

# Pehli baar abhi run karo
run_pipeline()

# Phir har din subah 8 baje
schedule.every().day.at("08:00").do(run_pipeline)

print("\n⏰ Scheduler started — runs daily at 8:00 AM")
print("Ctrl+C se band karo\n")

while True:
    schedule.run_pending()
    time.sleep(60)
from dotenv import load_dotenv
import os
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Debug
print(f"Key loaded: {repr(GROQ_API_KEY[:10]) if GROQ_API_KEY else 'NONE'}")
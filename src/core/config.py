from dotenv import load_dotenv
import os
from pathlib import Path
import logging

ROOT_DIR = Path(__file__).parent.parent.parent
env_loading_result = load_dotenv(ROOT_DIR / ".env")
if not env_loading_result:
    logging.warning(".env file not found or could not be loaded.")
else:
    logging.info(".env file loaded: %s", env_loading_result)

LLAMA_PARSER_API_KEY = os.getenv("LLAMA_PARSE_API_KEY") or ""
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or ""

STORAGE_DIR = ROOT_DIR / "data" / ".storage"

SCRAPPING_PAGE_CONTENT_LIMIT = 15000  # characters

GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE") or 0.7)

GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-2.0-flash"

REDIS_URL = os.getenv("REDIS_URL") or "redis://localhost:6379/0"

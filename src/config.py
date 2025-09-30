from dotenv import load_dotenv
import os
from pathlib import Path
from .logger import default_logger as logger

env_loading_result = load_dotenv(Path(__file__).parent.parent / ".env")
if not env_loading_result:
    logger.warning(".env file not found or could not be loaded.")
else:
    logger.info(".env file loaded: %s", env_loading_result)

LLAMA_PARSER_API_KEY = os.getenv("LLAMA_PARSE_API_KEY") or ""
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or ""

STORAGE_DIR = Path(__file__).parent.parent / "data" / ".storage"

SCRAPPING_PAGE_CONTENT_LIMIT = 15000  # characters

GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE") or 0.1)

GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-2.0-flash"

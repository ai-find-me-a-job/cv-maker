from pathlib import Path

from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).parent.parent.parent


class Config(BaseSettings):
    llama_parser_api_key: str = Field(alias="LLAMA_PARSE_API_KEY")
    google_api_key: str = Field(alias="GOOGLE_API_KEY")
    qdrant_key: str = Field(alias="QDRANT_KEY")
    qdrant_endpoint: str = Field(alias="QDRANT_ENDPOINT")
    scrapping_page_content_limit: int = 15000  # characters
    gemini_temperature: float = 0.7
    gemini_model: str = "gemini-2.0-flash"
    redis_dsn: RedisDsn = "redis://localhost:6379/0"
    supported_languages: dict = {"en": "English", "pt": "Portuguese (Brazilian)"}


config = Config(_env_file=ROOT_DIR / ".env", _env_file_encoding="utf-8")

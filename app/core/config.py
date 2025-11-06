from pathlib import Path

from google.genai.types import EmbedContentConfig
from pydantic import BaseModel, Field, RedisDsn
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).parent.parent.parent


class CustomEmbedConfig(EmbedContentConfig):
    task_type: str = "RETRIEVAL_QUERY"
    output_dimensionality: int = 768


class TextSplitterConfig(BaseModel):
    chunk_size: int = 1024
    chunk_overlap: int = 200


class Config(BaseSettings):
    llama_parser_api_key: str = Field(alias="LLAMA_PARSE_API_KEY")
    google_api_key: str = Field(alias="GOOGLE_API_KEY")
    qdrant_key: str = Field(alias="QDRANT_KEY")
    qdrant_endpoint: str = Field(alias="QDRANT_ENDPOINT")
    scrapping_page_content_limit: int = 15000  # characters
    gemini_temperature: float = 0.7
    gemini_model: str = "gemini-2.0-flash"
    redis_dsn: RedisDsn = "redis://localhost:6379/0"
    mongo_uri: str = Field(alias="MONGO_URI")
    supported_languages: dict = {"en": "English", "pt": "Portuguese (Brazilian)"}
    embed_config: CustomEmbedConfig = CustomEmbedConfig()
    text_splitter_config: TextSplitterConfig = TextSplitterConfig()


config = Config(_env_file=ROOT_DIR / ".env", _env_file_encoding="utf-8")

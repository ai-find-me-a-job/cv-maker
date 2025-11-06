from functools import lru_cache
from typing import Tuple

from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from qdrant_client import AsyncQdrantClient, QdrantClient

from app.core.config import config
from app.services.index_manager import VectorIndexManager


@lru_cache
def get_llm_model() -> GoogleGenAI:
    llm = GoogleGenAI(
        model=config.gemini_model,
        api_key=config.google_api_key,
        temperature=config.gemini_temperature,
    )
    return llm


@lru_cache()
def get_google_embed_model() -> GoogleGenAIEmbedding:
    embed_model = GoogleGenAIEmbedding(
        model="gemini-embedding-001",
        api_key=config.google_api_key,
        embedding_config=config.embed_config,
    )
    return embed_model


@lru_cache()
def get_qdrant_clients() -> Tuple[QdrantClient, AsyncQdrantClient]:
    qdrant_client = QdrantClient(url=config.qdrant_endpoint, api_key=config.qdrant_key)
    aqdrant_client = AsyncQdrantClient(
        url=config.qdrant_endpoint,
        api_key=config.qdrant_key,
    )
    return qdrant_client, aqdrant_client


def get_vector_index_manager_service() -> VectorIndexManager:
    return VectorIndexManager(
        embed_model=get_google_embed_model(), qdrant_clients=get_qdrant_clients()
    )

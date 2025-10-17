import logging as logger
from pathlib import Path
from typing import Sequence

from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
)
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_parse import LlamaParse, ResultType
from qdrant_client import AsyncQdrantClient

from .config import config


class VectorIndexManager:
    def __init__(self, collection_name: str = "rag-files") -> None:
        """Manage the vector index using Qdrant as the vector store."""
        self.collection_name = collection_name
        self.embed_model = GoogleGenAIEmbedding(
            model="gemini-embedding-001", api_key=config.google_api_key
        )
        self.qdrant_client = AsyncQdrantClient(
            url=config.qdrant_endpoint,
            api_key=config.qdrant_key,
        )
        self.index = self._load_or_create_index()

    def _load_or_create_index(self) -> VectorStoreIndex:
        vector_store = QdrantVectorStore(
            aclient=self.qdrant_client, collection_name=self.collection_name
        )
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=self.embed_model,
            use_async=True,
            store_nodes_override=True,
        )
        return index

    async def add_documents(self, file_paths: Sequence[str | Path]) -> None:
        parser = LlamaParse(  # type: ignore
            api_key=config.llama_parser_api_key,  # type: ignore
            result_type=ResultType.MD,
            verbose=True,
        )

        file_extractor = {".pdf": parser}
        files_to_add = []
        for file_path in file_paths:
            if await self._check_file_already_added(file_path):
                logger.warning(f"File {file_path} already added, skipping.")
                continue
            files_to_add.append(file_path)

        documents = await SimpleDirectoryReader(
            input_files=files_to_add,
            file_extractor=file_extractor,  # type: ignore
        ).aload_data()

        # Insert documents into existing index
        for doc in documents:
            await self.index.ainsert(doc)

    async def get_added_files(self) -> set:
        """Get list of filenames already in the vector store"""
        docs_info = self.index.ref_doc_info
        filenames = set()
        if docs_info is None:
            return filenames

        for doc in docs_info.values():
            if hasattr(doc, "metadata") and "file_name" in doc.metadata:
                filenames.add(doc.metadata["file_name"])

        return filenames

    async def _check_file_already_added(self, file_path: str | Path) -> bool:
        """Check if a file has already been added to the index"""
        added_files = await self.get_added_files()
        return Path(file_path).name in added_files

    def get_index(self) -> VectorStoreIndex:
        return self.index

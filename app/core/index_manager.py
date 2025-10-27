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
    """Manager for a vector index backed by Qdrant.

    This class wraps a Llama-Index VectorStoreIndex that uses Qdrant as the
    vector store implementation. It provides convenience methods to add files
    (documents) to the index, list files already added (by inspecting point
    payloads) and delete the underlying collection.
    """

    def __init__(self, collection_name: str = "rag-files") -> None:
        """Initialize resources for the vector index.

        Args:
            collection_name: Name of the Qdrant collection to use/create.

        Side effects:
            - Creates an AsyncQdrantClient using credentials from `config`.
            - Builds a Google embedding model instance.
            - Constructs a QdrantVectorStore wrapper and a VectorStoreIndex
              instance (async-enabled) that will be used for insert/query
              operations.
        """
        self.collection_name = collection_name
        self.embed_model = GoogleGenAIEmbedding(
            model="gemini-embedding-001", api_key=config.google_api_key
        )
        self.qdrant_client = AsyncQdrantClient(
            url=config.qdrant_endpoint,
            api_key=config.qdrant_key,
        )
        self.vector_store = QdrantVectorStore(
            aclient=self.qdrant_client, collection_name=self.collection_name
        )
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            embed_model=self.embed_model,
            use_async=True,
            store_nodes_override=True,
        )

    async def add_documents(self, file_paths: Sequence[str | Path]) -> list[str]:
        """Add files to the vector index.

        The method will:
        - Skip files that appear to have been already added (by file name).
        - Parse supported files (PDF via LlamaParse parser) into documents.
        - Insert the resulting documents (nodes) into the vector index.

        Args:
            file_paths: Iterable of file paths (strings or Path objects) to add.

        Returns:
            A list of file names that were accepted for insertion.
        """

        parser = LlamaParse(  # type: ignore
            api_key=config.llama_parser_api_key,  # type: ignore
            result_type=ResultType.MD,
            verbose=True,
        )
        already_added_files = await self.get_added_files()
        file_extractor = {".pdf": parser}
        files_to_add = []
        for file_path in file_paths:
            file_path = Path(file_path)
            if file_path.name in already_added_files:
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

        return [file.name for file in files_to_add]

    async def get_added_files(self) -> list[str]:
        """Return a list of filenames already present in the collection.

        The implementation inspects the Qdrant collection points payloads and
        returns the unique values of the `file_name` payload key. The list is
        returned as `list[str]` for simple consumption by callers.

        Note: This method performs a scroll request and may return up to the
        `limit` configured in the call. For very large collections, pagination
        would be required.
        """

        points = await self.qdrant_client.scroll(
            collection_name=self.collection_name,
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )

        files_set = set()
        for point in points[0]:
            payload = point.payload
            if not payload:
                continue
            files_set.add(payload.get("file_name"))

        # Return stable list (deduplicated)
        return list(files_set)

    def get_index(self) -> VectorStoreIndex:
        """Return the underlying VectorStoreIndex instance.

        This provides access for advanced operations not directly exposed by
        this manager wrapper.
        """

        return self.index

    async def delete_collection(self) -> None:
        """Delete the underlying Qdrant collection.

        Use this to remove all stored vectors and metadata for the configured
        collection. This operation is irreversible.
        """

        await self.qdrant_client.delete_collection(self.collection_name)

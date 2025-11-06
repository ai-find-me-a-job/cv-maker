import logging
from pathlib import Path

from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
)
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_parse import LlamaParse, ResultType
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http.models import Distance, PayloadSchemaType, VectorParams

from app.core.config import config
from app.models.index import DocumentModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorIndexManager:
    """Manager for a vector index backed by Qdrant.

    This class wraps a Llama-Index VectorStoreIndex that uses Qdrant as the
    vector store implementation. It provides convenience methods to add files
    (documents) to the index, list files already added (by inspecting point
    payloads) and delete the underlying collection.
    """

    def __init__(
        self,
        embed_model: BaseEmbedding,
        qdrant_clients: tuple[QdrantClient, AsyncQdrantClient],
        vecstore_collection_name: str = "rag-files",
    ) -> None:
        """Initialize resources for the vector index.

        Args:
            vecstore_collection_name: Name of the Qdrant collection to use/create.
            embed_model: The embedding model to use for vectorizing documents.
            qdrant_clients: A tuple containing synchronous and asynchronous Qdrant clients.


        Side effects:
            - Constructs a QdrantVectorStore wrapper and a VectorStoreIndex
              instance (async-enabled) that will be used for insert/query
              operations.
        """
        self.collection_name = vecstore_collection_name
        self.embed_model = embed_model
        self.qdrant_client, self.aqdrant_client = qdrant_clients
        self._create_qdrant_collection_if_not_exists()
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            aclient=self.aqdrant_client,
            collection_name=self.collection_name,
        )
        self._index = VectorStoreIndex.from_vector_store(
            self.vector_store,
            embed_model=self.embed_model,
            use_async=True,
            override_store_nodes=False,
        )

    def _create_qdrant_collection_if_not_exists(self) -> None:
        if not self.qdrant_client.collection_exists(self.collection_name):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "text-dense": VectorParams(
                        size=config.embed_config.output_dimensionality,
                        distance=Distance.COSINE,
                    )
                },
            )
            self.qdrant_client.create_payload_index(
                collection_name=self.collection_name,
                field_name="ref_doc_id",
                field_schema=PayloadSchemaType.UUID,
            )
            self.qdrant_client.create_payload_index(
                collection_name=self.collection_name,
                field_name="doc_id",
                field_schema=PayloadSchemaType.UUID,
            )

    async def add_document(self, file_path: str | Path) -> DocumentModel:
        """Add file to docstore and vector index.

        The method will:
        - Skip files that appear to have been already added (by file name).
        - Parse supported files (PDF via LlamaParse parser) into documents.
        - Insert the resulting documents (nodes) into the vector index.

        Args:
            file_path: The file path (string or Path object) to add.

        Returns:
            list[DocumentModel]: Information about the added documents (one file can generate more than one document).
        """

        parser = LlamaParse(  # type: ignore
            api_key=config.llama_parser_api_key,  # type: ignore
            result_type=ResultType.MD,
            verbose=True,
        )
        text_splitter = SentenceSplitter(
            chunk_size=config.text_splitter_config.chunk_size,
            chunk_overlap=config.text_splitter_config.chunk_overlap,
        )
        file_extractor = {
            ".pdf": parser,
            ".jpg": parser,
            ".jpeg": parser,
            ".png": parser,
        }
        file_path = Path(file_path)

        documents = await SimpleDirectoryReader(
            input_files=[file_path],
            file_extractor=file_extractor,  # type: ignore
        ).aload_data()

        nodes = await text_splitter.aget_nodes_from_documents(documents=documents)
        # BUG: Nodes are coming with different ref_doc_id
        # Insert documents into existing index
        main_node = nodes[0]
        if not main_node.ref_doc_id:
            raise ValueError("Main node does not have a reference document ID.")

        document_representation = DocumentModel(
            ref_doc_id=main_node.ref_doc_id,
            file_name=main_node.metadata.get("file_name", "unknown"),
            file_type=main_node.metadata.get("file_type", "unknown"),
            file_size=main_node.metadata.get("file_size", 0),
            creation_date=main_node.metadata.get("creation_date", 0),
            last_modified_date=main_node.metadata.get("last_modified_date", 0),
            node_ids=[node.id_ for node in nodes],
        )
        await self._index.ainsert_nodes(nodes=nodes)
        return document_representation

    async def get_all_documents(self) -> list[DocumentModel]:
        """Retrieve all documents stored in the document store.

        Returns:
            list[DocumentModel]: List of documents stored in the document store.
        """

        all_nodes = await self.vector_store.aget_nodes()
        ref_doc_hash_map: dict[str, DocumentModel] = {}
        for node in all_nodes:
            ref_doc_id = node.ref_doc_id
            if ref_doc_id is None:
                logger.warning(f"Node {node.id_} has no ref_doc_id; skipping.")
                continue
            if ref_doc_id not in ref_doc_hash_map:
                ref_doc_hash_map[ref_doc_id] = DocumentModel(
                    ref_doc_id=ref_doc_id, node_ids=[], **node.metadata
                )

            ref_doc_hash_map[ref_doc_id].node_ids.append(node.id_)

        if not ref_doc_hash_map:
            return []

        return list(ref_doc_hash_map.values())

    async def get_document(self, ref_doc_id: str) -> DocumentModel:
        """Retrieve a document from the document store by its ID.

        Args:
            doc_id: The ID of the document to retrieve.
        Returns:
            DocumentModel: The document with the specified ID.
        Raises:
            KeyError: If the document with the specified ID is not found.
            ValueError: If the main node does not have a reference document ID.
        """
        nodes_filter = MetadataFilters(
            filters=[
                ExactMatchFilter(key="ref_doc_id", value=ref_doc_id),
            ]
        )
        nodes = await self.vector_store.aget_nodes(filters=nodes_filter)
        if not nodes:
            raise KeyError(f"Document with ID {ref_doc_id} not found.")
        main_node = nodes[0]
        if not main_node.ref_doc_id:
            raise ValueError("Main node does not have a reference document ID.")

        document_representation = DocumentModel(
            ref_doc_id=main_node.ref_doc_id,
            file_name=main_node.metadata.get("file_name", "unknown"),
            file_type=main_node.metadata.get("file_type", "unknown"),
            file_size=main_node.metadata.get("file_size", 0),
            creation_date=main_node.metadata.get("creation_date", 0),
            last_modified_date=main_node.metadata.get("last_modified_date", 0),
            node_ids=[node.id_ for node in nodes],
        )
        return document_representation

    async def delete_all_documents(self) -> None:
        """Delete the underlying Qdrant collection and DocStore.

        Use this to remove all stored vectors and metadata for the configured
        collection. This operation is irreversible.
        """

        await self.vector_store.adelete_nodes()

    async def delete_document(self, ref_doc_id: str) -> None:
        """Delete a specific document from the index and docstore.
        Args:
            ref_doc_id: The ID of the document to delete.
        """

        await self.vector_store.adelete(ref_doc_id=ref_doc_id)

    def get_index(self) -> VectorStoreIndex:
        """Return the underlying VectorStoreIndex instance.

        This provides access for advanced operations not directly exposed by
        this manager wrapper.
        """
        return self._index

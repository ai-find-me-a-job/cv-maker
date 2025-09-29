from llama_parse import LlamaParse, ResultType
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from pathlib import Path
from src.config import GOOGLE_API_KEY, LLAMA_PARSER_API_KEY, STORAGE_DIR
from src.logger import default_logger as logger


class VectorIndexManager:
    def __init__(self, storage_dir: str | None = None) -> None:
        if storage_dir is None:
            self.storage_dir = STORAGE_DIR
        else:
            self.storage_dir = storage_dir

        self.embed_model = GoogleGenAIEmbedding(
            model="embedding-001", api_key=GOOGLE_API_KEY
        )
        self.index = self._load_or_create_index()

    def _load_or_create_index(self) -> VectorStoreIndex:
        if Path(self.storage_dir).exists():
            storage_context = StorageContext.from_defaults(
                persist_dir=str(self.storage_dir)
            )
            return load_index_from_storage(
                storage_context, embed_model=self.embed_model
            )  # type: ignore
        else:
            return VectorStoreIndex([], embed_model=self.embed_model)

    def add_documents(self, file_paths: list[str | Path]) -> None:
        parser = LlamaParse(  # type: ignore
            api_key=LLAMA_PARSER_API_KEY,  # type: ignore
            result_type=ResultType.MD,
            verbose=True,
        )

        file_extractor = {".pdf": parser}

        for file_path in file_paths:
            if self._check_file_already_added(file_path):
                logger.warning(f"File {file_path} already added, skipping.")
                continue

            documents = SimpleDirectoryReader(
                input_files=[file_path],
                file_extractor=file_extractor,  # type: ignore
            ).load_data()

            # Insert documents into existing index
            for doc in documents:
                self.index.insert(doc)

        # Persist the updated index
        self.index.storage_context.persist(persist_dir=self.storage_dir)

    def get_added_files(self) -> set:
        """Get list of filenames already in the vector store"""
        if not hasattr(self.index, "docstore") or not self.index.docstore.docs:
            return set()

        filenames = set()
        for doc in self.index.docstore.docs.values():
            if hasattr(doc, "metadata") and "file_name" in doc.metadata:
                filenames.add(doc.metadata["file_name"])

        return filenames

    def _check_file_already_added(self, file_path: str | Path) -> bool:
        """Check if a file has already been added to the index"""
        added_files = self.get_added_files()
        return Path(file_path).name in added_files

    def get_index(self) -> VectorStoreIndex:
        return self.index

from pathlib import Path

from app.core.index_manager import VectorIndexManager


async def add_files_to_index(file_paths: list[str | Path]) -> list[str]:
    index_manager = VectorIndexManager()
    added_files = await index_manager.add_documents(file_paths)
    return added_files


async def get_files_in_index() -> list[str]:
    index_manager = VectorIndexManager()
    all_files = await index_manager.get_added_files()
    return all_files


async def delete_vector_index_collection() -> None:
    index_manager = VectorIndexManager()
    await index_manager.delete_collection()

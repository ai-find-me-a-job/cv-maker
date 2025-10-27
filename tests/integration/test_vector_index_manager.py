from pathlib import Path

import pytest
from qdrant_client.models import Distance, VectorParams

from app.core.config import config
from app.core.index_manager import VectorIndexManager


@pytest.fixture
async def vector_index_manager():
    """Fixture that creates a test collection and cleans it up after the test."""
    collection_name = "test-rag-files"
    vector_idx_mng = VectorIndexManager(collection_name=collection_name)

    # Create collection with proper vector configuration
    await vector_idx_mng.aqdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "text-dense": VectorParams(
                size=config.embed_config.output_dimensionality, distance=Distance.COSINE
            )
        },
    )

    yield vector_idx_mng

    # Cleanup
    await vector_idx_mng.aqdrant_client.delete_collection(collection_name)


@pytest.mark.asyncio
async def test_add_documents(vector_index_manager: VectorIndexManager):
    """Test adding documents to the vector index."""
    test_files = [Path(__file__).parent / "sample_files" / "test_file.md"]

    # Add documents
    added_documents = await vector_index_manager.add_documents(test_files)
    print(added_documents)
    # Verify documents were added by checking the collection info
    collection_info = await vector_index_manager.aqdrant_client.get_collection(
        vector_index_manager.collection_name
    )
    added_files = await vector_index_manager.get_added_files()
    print(added_files)
    # Assert that at least one vector was added (the test file should produce at least one chunk)
    assert collection_info.points_count is not None, "Collection points count is None"
    assert collection_info.points_count > 0, "No documents were added to the collection"
    assert all([doc in added_files for doc in added_documents]), (
        "Not all added documents are in the collection"
    )

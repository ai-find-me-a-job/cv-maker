from pathlib import Path

import pytest

from app.services.index_manager import VectorIndexManager


@pytest.fixture
async def vector_index_manager():
    """Fixture that creates a test collection and cleans it up after the test."""
    collection_name = "test-rag-files"
    vector_idx_mng = VectorIndexManager(vecstore_collection_name=collection_name)

    yield vector_idx_mng

    # Cleanup
    await vector_idx_mng.aqdrant_client.delete_collection(collection_name)


@pytest.mark.asyncio
async def test_add_documents(vector_index_manager: VectorIndexManager):
    """Test adding documents to the vector index."""
    test_file = Path(__file__).parent / "sample_files" / "test_file.md"

    # Add documents
    added_document = await vector_index_manager.add_document(test_file)

    # Verify documents were added by checking the collection info
    collection_info = await vector_index_manager.aqdrant_client.get_collection(
        vector_index_manager.collection_name
    )
    added_file = await vector_index_manager.get_document(
        ref_doc_id=added_document.ref_doc_id
    )
    # Assert that at least one vector was added (the test file should produce at least one chunk)
    assert collection_info.points_count is not None, "Collection points count is None"
    assert collection_info.points_count > 0, "No documents were added to the collection"
    assert added_document.model_dump() == added_file.model_dump()

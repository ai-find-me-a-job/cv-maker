import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.factories import get_vector_index_manager_service
from app.models.index import DocumentModel
from app.services.index_manager import VectorIndexManager

logger = logging.getLogger()

router = APIRouter(prefix="/cv/index", tags=["Index Management"])


@router.post("/documents", response_model=DocumentModel)
async def add_file_to_index(
    file: UploadFile = File(...),
    index_manager: VectorIndexManager = Depends(get_vector_index_manager_service),
):
    """
    Add uploaded files to the vector index for CV generation.

    This endpoint accepts file uploads, saves them as temporary files,
    adds them to the vector index, and then removes the temporary files.

    Supported file types: PDF, DOCX, TXT, and other document formats
    supported by the document index.
    """
    added_files = []

    try:
        # Save uploaded files as temporary files
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f"_{file.filename}", delete_on_close=True
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)
            logger.info(f"Saved temporary file: {temp_file_path}")
            # Add files to index
            logger.info(f"Adding {temp_file_path} files to vector index")
            added_files = await index_manager.add_document(temp_file_path)

        return added_files

    except Exception as e:
        logger.error(f"Error adding files to index: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add files: {str(e)}")


@router.get("/documents", response_model=list[DocumentModel])
async def get_all_documents(
    index_manager: VectorIndexManager = Depends(get_vector_index_manager_service),
):
    """
    Retrieve a list of files currently stored in the vector index.

    Returns:
        List of file names or paths in the index.
    """
    try:
        all_docs = await index_manager.get_all_documents()
        return all_docs
    except Exception as e:
        logger.error(f"Error retrieving files from index: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve files: {str(e)}"
        )


@router.get("/documents/{ref_doc_id}", response_model=DocumentModel)
async def get_document_by_id(
    ref_doc_id: str,
    index_manager: VectorIndexManager = Depends(get_vector_index_manager_service),
):
    """
    Retrieve a document from the vector index by its ID.

    Args:
        ref_doc_id (str): The ID of the document to retrieve.
    """
    try:
        document = await index_manager.get_document(ref_doc_id)
        return document
    except KeyError as e:
        logger.error(f"Document not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve document: {str(e)}"
        )


@router.delete("/documents", status_code=204)
async def delete_all_documents(
    index_manager: VectorIndexManager = Depends(get_vector_index_manager_service),
):
    """
    Delete all documents.

    This endpoint removes all data from the vector index.
    Use with caution as this action is irreversible.
    """
    try:
        await index_manager.delete_all_documents()
    except Exception as e:
        logger.error(f"Error deleting vector index collection: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete collection: {str(e)}"
        )


@router.delete("/documents/{ref_doc_id}", status_code=204)
async def delete_document(
    ref_doc_id: str,
    index_manager: VectorIndexManager = Depends(get_vector_index_manager_service),
):
    """
    Delete a specific document from the vector index.

    Args:
        doc_id (str): The ID of the document to delete.
    """
    try:
        # await index_manager.delete_document(doc_id)
        await index_manager.delete_document(ref_doc_id=ref_doc_id)
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete document: {str(e)}"
        )

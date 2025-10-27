import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.index import AddedFilesResponse
from app.services import (
    add_files_to_index,
    delete_vector_index_collection,
    get_files_in_index,
)

logger = logging.getLogger()

router = APIRouter(prefix="/cv/index", tags=["Index Management"])


@router.post("/files", response_model=AddedFilesResponse)
async def add_files_to_vector_index(files: list[UploadFile] = File(...)):
    """
    Add uploaded files to the vector index for CV generation.

    This endpoint accepts file uploads, saves them as temporary files,
    adds them to the vector index, and then removes the temporary files.

    Supported file types: PDF, DOCX, TXT, and other document formats
    supported by the document index.
    """
    temp_files = []
    added_files = []

    try:
        # Save uploaded files as temporary files
        for file in files:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f"_{file.filename}"
            ) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = Path(temp_file.name)
                temp_files.append(temp_file_path)
                logger.info(f"Saved temporary file: {temp_file_path}")

        # Add files to index
        logger.info(f"Adding {len(temp_files)} files to vector index")
        added_files = await add_files_to_index(temp_files)

        return AddedFilesResponse(added_files=added_files)

    except Exception as e:
        logger.error(f"Error adding files to index: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add files: {str(e)}")

    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"Removed temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file}: {e}")


@router.get("/files", response_model=AddedFilesResponse)
async def get_files():
    """
    Retrieve a list of files currently stored in the vector index.

    Returns:
        List of file names or paths in the index.
    """
    try:
        files_in_index = await get_files_in_index()
        return AddedFilesResponse(added_files=files_in_index)
    except Exception as e:
        logger.error(f"Error retrieving files from index: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve files: {str(e)}"
        )


@router.delete("/collection", status_code=204)
async def delete_collection():
    """
    Delete the entire vector index collection.

    This endpoint removes all data from the vector index.
    Use with caution as this action is irreversible.
    """
    try:
        await delete_vector_index_collection()
    except Exception as e:
        logger.error(f"Error deleting vector index collection: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete collection: {str(e)}"
        )

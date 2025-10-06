from fastapi import APIRouter, HTTPException, UploadFile, File
from src.models.index import AddFilesResponse
from src.services import add_files_to_index
from pathlib import Path
import logging
import tempfile


logger = logging.getLogger()

router = APIRouter(prefix="/cv/index", tags=["Index Management"])


@router.post("/add-files", response_model=AddFilesResponse)
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

        return AddFilesResponse(added_files=added_files)

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

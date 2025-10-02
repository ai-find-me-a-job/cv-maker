from fastapi import APIRouter, HTTPException, Body
from .schemas import (
    CVWorkflowResponse,
    JobUrlRequest,
)
import logging

from src.cv_maker.services import run_cv_workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cv", tags=["CV Generation"])


@router.post("/generate/from-description", response_model=CVWorkflowResponse)
async def generate_cv_from_description(
    job_description: str = Body(
        ..., description="Job description text", media_type="text/plain"
    ),
):
    """
    Generate a CV based on a job description text.
    """
    try:
        logger.info("Starting CV generation from job description")
        result = await run_cv_workflow(job_description=job_description)
        return CVWorkflowResponse(
            latex_content=result.latex_content, pdf_path=result.pdf_path
        )
    except Exception as e:
        logger.error(f"Error generating CV from description: {e}")
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")


@router.post("/generate/from-url", response_model=CVWorkflowResponse)
async def generate_cv_from_url(request: JobUrlRequest):
    """
    Generate a CV by scraping a job posting from a URL.
    """
    try:
        logger.info(f"Starting CV generation from job URL: {request.job_url}")
        result = await run_cv_workflow(job_url=request.job_url)
        return CVWorkflowResponse(
            latex_content=result.latex_content, pdf_path=result.pdf_path
        )
    except Exception as e:
        logger.error(f"Error generating CV from URL: {e}")
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")

from fastapi import APIRouter, HTTPException, Body
from src.models.cv import (
    StartCVWorkflowResponse,
    JobUrlRequest,
    ContinueCVWorkflowResponse,
    ContinueCVWorkflowRequest,
)
import logging

from src.services import start_cv_workflow, continue_cv_workflow


logger = logging.getLogger()

router = APIRouter(prefix="/cv", tags=["CV Generation"])


@router.post("/run/from-description", response_model=StartCVWorkflowResponse)
async def run_cv_from_description(
    job_description: str = Body(
        ..., description="Job description text", media_type="text/plain"
    ),
):
    """
    Generate a CV based on a job description text.
    """
    try:
        logger.info("Starting CV generation from job description")
        result = await start_cv_workflow(job_description=job_description)
        return result
    except Exception as e:
        logger.error(f"Error generating CV from description: {e}")
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")


@router.post("/run/from-url", response_model=StartCVWorkflowResponse)
async def run_cv_from_url(request: JobUrlRequest):
    """
    Generate a CV by scraping a job posting from a URL.
    """
    try:
        logger.info(f"Starting CV generation from job URL: {request.job_url}")
        result = await start_cv_workflow(job_url=request.job_url)
        return result
    except Exception as e:
        logger.error(f"Error generating CV from URL: {e}")
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")


@router.post("/continue/{workflow_id}", response_model=ContinueCVWorkflowResponse)
async def continue_from_id(workflow_id: str, request: ContinueCVWorkflowRequest):
    """
    Continue a CV generation workflow.
    """
    try:
        logger.info(f"Continuing CV workflow: {workflow_id}")
        result = await continue_cv_workflow(
            workflow_id=workflow_id, **request.model_dump()
        )
        return result
    except Exception as e:
        logger.error(f"Error continuing CV workflow: {e}")
        raise HTTPException(
            status_code=500, detail=f"CV workflow continuation failed: {str(e)}"
        )

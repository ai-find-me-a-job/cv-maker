import logging

from fastapi import APIRouter, Body, HTTPException

from app.core.config import SUPPORTED_LANGUAGES
from app.models.cv import (
    ContinueCVWorkflowRequest,
    ContinueCVWorkflowResponse,
    JobUrlRequest,
    StartCVWorkflowResponse,
    SupportedLanguagesResponse,
)
from app.services import continue_cv_workflow, start_cv_workflow

logger = logging.getLogger()

router = APIRouter(prefix="/cv", tags=["CV Generation"])


def validate_language(language: str) -> str:
    """Validate and return the language code if supported."""
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{language}'. Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}",
        )
    return language


@router.get("/languages", response_model=SupportedLanguagesResponse)
async def get_supported_languages():
    """
    Get the list of supported languages for CV generation.
    """
    return SupportedLanguagesResponse(languages=SUPPORTED_LANGUAGES)


@router.post("/run/from-description/{language}", response_model=StartCVWorkflowResponse)
async def run_cv_from_description(
    language: str,
    job_description: str = Body(
        ..., description="Job description text", media_type="text/plain"
    ),
):
    """
    Generate a CV based on a job description text.

    Parameters:
    - language: Language code ('en' for English, 'pt' for Portuguese)
    """
    try:
        validated_language = validate_language(language)

        logger.info("Starting CV generation from job description")
        result = await start_cv_workflow(
            job_description=job_description, language=validated_language
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating CV from description: {e}")
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")


@router.post("/run/from-url/{language}", response_model=StartCVWorkflowResponse)
async def run_cv_from_url(language: str, request: JobUrlRequest):
    """
    Generate a CV by scraping a job posting from a URL.

    Parameters:
    - language: Language code ('en' for English, 'pt' for Portuguese)
    """
    try:
        validated_language = validate_language(language)

        logger.info(f"Starting CV generation from job URL: {request.job_url}")
        result = await start_cv_workflow(
            job_url=request.job_url, language=validated_language
        )
        return result
    except HTTPException:
        raise
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

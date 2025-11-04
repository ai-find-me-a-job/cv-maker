import json
import logging
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException
from llama_index.core.workflow import Context
from redis.asyncio import Redis

from app.core.config import config
from app.core.exceptions import StorageError, WorkFlowError
from app.core.index_manager import VectorIndexManager
from app.models.cv import (
    ContinueCVWorkflowRequest,
    ContinueCVWorkflowResponse,
    JobUrlRequest,
    StartCVWorkflowResponse,
    SupportedLanguagesResponse,
)
from app.services.workflow import CVStopEvent, CVWorkflow
from app.services.workflow.events import AskForCVReviewEvent, CVReviewResponseEvent

logger = logging.getLogger()

router = APIRouter(prefix="/cv", tags=["CV Generation"])


async def start_cv_workflow(
    job_url: str | None = None, job_description: str | None = None, language: str = "en"
) -> StartCVWorkflowResponse:
    """
    Asynchronously starts a CV workflow based on a provided job URL or job description.
    When the workflow reaches a point where it requires human review, it generates a unique
    workflow ID, stores the current workflow context in Redis, and returns the LaTeX content
    for review.

    Parameters:
        job_url (str | None): The URL of the job posting. If provided, it will be used to inform the workflow.
            Defaults to None.
        job_description (str | None): A textual description of the job. If provided, it will be used to inform
            the workflow. Defaults to None.

    Returns:
        StartCVWorkflowResponse: An object containing the status ("review_needed"), a unique workflow ID,
            and the LaTeX content for review.

    Raises:
        WorkFlowError: If the workflow completes without triggering an AskForCVReviewEvent.
    """
    redis_client = Redis.from_url(str(config.redis_dsn), decode_responses=True)
    workflow = CVWorkflow(timeout=600)

    workflow_handler = workflow.run(
        job_url=job_url, job_description=job_description, language=language
    )
    async for event in workflow_handler.stream_events():
        if isinstance(event, AskForCVReviewEvent):
            workflow_id = str(uuid4())
            if workflow_handler.ctx is None:
                raise WorkFlowError("Workflow context is missing.")
            workflow_ctx = workflow_handler.ctx.to_dict()
            await redis_client.set(
                name=f"cv_workflow:{workflow_id}", value=json.dumps(workflow_ctx)
            )
            return StartCVWorkflowResponse(
                status="review_needed",
                workflow_id=workflow_id,
                latex_content=event.latex_content,
            )

    raise WorkFlowError("CV Workflow did not ask for review.")


async def continue_cv_workflow(
    workflow_id: str, approve: bool, feedback: str | None = None
) -> ContinueCVWorkflowResponse:
    """
    Continues a CV workflow by processing a review response and advancing the workflow state.
    This function retrieves the stored workflow context from Redis, resumes the CVWorkflow,
    sends a CVReviewResponseEvent based on the approval and feedback, and streams events
    until completion or a review is needed again. It handles cleanup of the stored context
    upon completion.
    Args:
        workflow_id (str): The unique identifier of the CV workflow to continue.
        approve (bool): Indicates whether the CV is approved (True) or not (False).
        feedback (str | None, optional): Additional feedback for the review. Defaults to None.
    Returns:
        ContinueCVWorkflowResponse: An object containing the status of the workflow continuation,
        the workflow ID, and the LaTeX content of the CV. Status can be "completed" or "review_needed".
    Raises:
        StorageError: If no workflow is found with the given workflow_id.
        WorkFlowError: If the CV workflow does not complete properly.
    """

    redis_client = Redis.from_url(str(config.redis_dsn), decode_responses=True)
    workflow_ctx = await redis_client.get(f"cv_workflow:{workflow_id}")
    if not workflow_ctx:
        raise StorageError(f"No workflow found with ID: {workflow_id}")

    workflow = CVWorkflow(timeout=600)
    ctx = Context.from_dict(workflow=workflow, data=json.loads(workflow_ctx))
    workflow_handler = workflow.run(ctx=ctx)
    if workflow_handler.ctx is None:
        raise WorkFlowError("Workflow context is missing.")
    workflow_handler.ctx.send_event(
        CVReviewResponseEvent(approve=approve, feedback=feedback)
    )
    async for event in workflow_handler.stream_events():
        if isinstance(event, CVStopEvent):
            # Clean up the stored context
            await redis_client.delete(f"cv_workflow:{workflow_id}")
            return ContinueCVWorkflowResponse(
                status="completed",
                workflow_id=workflow_id,
                latex_content=event.latex_content,
            )
        elif isinstance(event, AskForCVReviewEvent):
            if workflow_handler.ctx is None:
                raise WorkFlowError("Workflow context is missing.")
            workflow_ctx = workflow_handler.ctx.to_dict()
            await redis_client.set(
                name=f"cv_workflow:{workflow_id}", value=json.dumps(workflow_ctx)
            )
            return ContinueCVWorkflowResponse(
                status="review_needed",
                workflow_id=workflow_id,
                latex_content=event.latex_content,
            )

    raise WorkFlowError("CV Workflow did not complete properly.")


def validate_language(language: str) -> str:
    """Validate and return the language code if supported."""
    if language not in config.supported_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{language}'. Supported languages: {', '.join(config.supported_languages.keys())}",
        )
    return language


@router.get("/languages", response_model=SupportedLanguagesResponse)
async def get_supported_languages():
    """
    Get the list of supported languages for CV generation.
    """
    return SupportedLanguagesResponse(languages=config.supported_languages)


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

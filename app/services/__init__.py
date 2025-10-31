import json
from pathlib import Path
from uuid import uuid4

from llama_index.core.workflow import Context
from redis.asyncio import Redis

from app.core.config import config
from app.core.exceptions import StorageError, WorkFlowError
from app.core.index_manager import VectorIndexManager
from app.models.cv import ContinueCVWorkflowResponse, StartCVWorkflowResponse

from .workflow import CVStopEvent, CVWorkflow
from .workflow.events import AskForCVReviewEvent, CVReviewResponseEvent


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

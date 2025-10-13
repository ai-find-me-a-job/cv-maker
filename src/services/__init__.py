from .workflow import CVWorkflow, CVStopEvent
from llama_index.core.workflow import Context
from .workflow.custom_events import AskForCVReviewEvent, CVReviewResponseEvent
from src.core.index_manager import VectorIndexManager
from pathlib import Path
from src.core.config import REDIS_URL
from redis import Redis
from uuid import uuid4
from src.core.exceptions import WorkFlowError, StorageError
import json


async def run_cv_workflow(
    job_url: str | None = None, job_description: str | None = None
) -> dict[str, str]:
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    workflow = CVWorkflow(timeout=600)

    workflow_handler = workflow.run(job_url=job_url, job_description=job_description)
    async for event in workflow_handler.stream_events():
        if isinstance(event, AskForCVReviewEvent):
            # Here you would normally send the resume to the user for review
            # For this example, we'll auto-approve it
            workflow_id = str(uuid4())
            workflow_ctx = workflow_handler.ctx.to_dict()
            # TODO: Move redis to async after
            redis_client.set(
                name=f"cv_workflow:{workflow_id}", value=json.dumps(workflow_ctx)
            )
            return {
                "workflow_id": workflow_id,
                "latex_content": event.latex_content,
                "pdf_path": event.pdf_path,
            }

    raise WorkFlowError("CV Workflow did not ask for review.")


async def continue_cv_workflow(
    workflow_id: str, approve: bool, feedback: str | None = None
) -> dict[str, str]:
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    workflow_ctx = redis_client.get(f"cv_workflow:{workflow_id}")
    if not workflow_ctx:
        raise StorageError(f"No workflow found with ID: {workflow_id}")

    workflow = CVWorkflow(timeout=600)
    ctx = Context.from_dict(workflow=workflow, data=json.loads(workflow_ctx))
    workflow_handler = workflow.run(ctx=ctx)
    workflow_handler.ctx.send_event(
        CVReviewResponseEvent(approve=approve, feedback=feedback)
    )
    async for event in workflow_handler.stream_events():
        if isinstance(event, CVStopEvent):
            # Clean up the stored context
            redis_client.delete(f"cv_workflow:{workflow_id}")
            return {
                "status": "completed",
                "latex_content": event.latex_content,
                "resume": event.resume.model_dump_json(),
            }
        elif isinstance(event, AskForCVReviewEvent):
            workflow_ctx = workflow_handler.ctx.to_dict()
            # TODO: Move redis to async after
            redis_client.set(
                name=f"cv_workflow:{workflow_id}", value=json.dumps(workflow_ctx)
            )
            return {
                "status": "review_needed",
                "workflow_id": workflow_id,
                "latex_content": event.latex_content,
                "pdf_path": event.pdf_path,
            }

    raise WorkFlowError("CV Workflow did not complete properly.")


async def add_files_to_index(file_paths: list[str | Path]) -> list[str]:
    index_manager = VectorIndexManager()
    index_manager.add_documents(file_paths)
    return list(index_manager.get_added_files())

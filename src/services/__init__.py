from .workflow import CVWorkflow, CVStopEvent
from .workflow.custom_events import AskForCVReviewEvent, CVReviewResponseEvent
from src.core.index_manager import VectorIndexManager
from pathlib import Path
import logging


async def run_cv_workflow(
    job_url: str | None = None, job_description: str | None = None
) -> CVStopEvent:
    workflow = CVWorkflow(timeout=600)

    workflow_handler = workflow.run(job_url=job_url, job_description=job_description)
    async for event in workflow_handler.stream_events():
        if isinstance(event, AskForCVReviewEvent):
            # Here you would normally send the resume to the user for review
            # For this example, we'll auto-approve it
            logging.info("Asking for CV review...")
            feedback = input(
                "Provide feedback for the resume (or press Enter to approve):"
            )
            approve = not bool(feedback)
            response = CVReviewResponseEvent(
                approve=approve, feedback=feedback if feedback else ""
            )
            workflow_handler.ctx.send_event(response)

    result = await workflow_handler
    return result


async def add_files_to_index(file_paths: list[str | Path]) -> list[str]:
    index_manager = VectorIndexManager()
    index_manager.add_documents(file_paths)
    return list(index_manager.get_added_files())

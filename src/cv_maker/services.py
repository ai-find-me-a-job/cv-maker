from src.cv_maker.workflow import CVWorkflow, CVStopEvent
from src.core.index_manager import VectorIndexManager
from pathlib import Path


async def run_cv_workflow(
    job_url: str | None = None, job_description: str | None = None
) -> CVStopEvent:
    workflow = CVWorkflow()
    result = await workflow.run(job_url=job_url, job_description=job_description)
    return result


async def add_files_to_index(file_paths: list[str | Path]) -> list[str]:
    index_manager = VectorIndexManager()
    index_manager.add_documents(file_paths)
    return list(index_manager.get_added_files())

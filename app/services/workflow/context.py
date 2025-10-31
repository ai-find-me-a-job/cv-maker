from pydantic import BaseModel, Field

from .extraction_models import CandidateInfo, Resume


class CVWorkflowState(BaseModel):
    """State model for the CV workflow."""

    language: str = Field(default="en")
    job_description: str = Field(default="No Job Description Provided")
    candidate_info: CandidateInfo | None = Field(default=None)
    feedback: str = Field(default="No Feedback Provided")
    resume: Resume | None = Field(default=None)
    latex_content: str = Field(default="")

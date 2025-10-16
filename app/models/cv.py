from pydantic import BaseModel


class JobDescriptionRequest(BaseModel):
    job_description: str


class JobUrlRequest(BaseModel):
    job_url: str


class SupportedLanguagesResponse(BaseModel):
    languages: dict[str, str]  # language_code -> display_name


class StartCVWorkflowResponse(BaseModel):
    status: str
    workflow_id: str
    latex_content: str


class ContinueCVWorkflowResponse(StartCVWorkflowResponse): ...


class ContinueCVWorkflowRequest(BaseModel):
    approve: bool
    feedback: str | None = None

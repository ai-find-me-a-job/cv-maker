from pydantic import BaseModel


class JobDescriptionRequest(BaseModel):
    job_description: str


class JobUrlRequest(BaseModel):
    job_url: str


class CVWorkflowResponse(BaseModel):
    latex_content: str
    pdf_path: str | None = None


class AddFilesRequest(BaseModel):
    file_paths: list[str]


class AddFilesResponse(BaseModel):
    added_files: list[str]

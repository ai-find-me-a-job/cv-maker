from pydantic import BaseModel


class AddFilesRequest(BaseModel):
    file_paths: list[str]


class AddFilesResponse(BaseModel):
    added_files: list[str]

from pydantic import BaseModel


class AddFilesRequest(BaseModel):
    file_paths: list[str]


class AddedFilesResponse(BaseModel):
    added_files: list[str]

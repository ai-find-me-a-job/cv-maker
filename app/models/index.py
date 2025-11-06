from datetime import date

from pydantic import BaseModel


class DocumentModel(BaseModel):
    ref_doc_id: str
    file_name: str
    file_type: str
    file_size: int
    creation_date: date
    last_modified_date: date
    node_ids: list[str]

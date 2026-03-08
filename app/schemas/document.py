from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    chroma_collection: str
    created_at: str

from pydantic import BaseModel


class PromptTemplateRequest(BaseModel):
    title: str
    content: str


class PromptTemplateResponse(BaseModel):
    id: str
    title: str
    content: str
    created_at: str

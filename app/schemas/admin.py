from pydantic import BaseModel


class FaqItem(BaseModel):
    question: str
    count: int


class GapItem(BaseModel):
    question: str
    count: int
    last_asked_at: str | None

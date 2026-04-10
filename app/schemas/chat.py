from pydantic import BaseModel


class HistoryMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    plan_context: str | None = None
    collection: str | None = None
    history: list[HistoryMessage] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    response_time_ms: int
    model_used: str
    embedding_model: str
    retrieval_strategy: str
    chunk_size: int
    chunks_retrieved: int


class ChatHistoryItem(BaseModel):
    id: str
    question: str
    answer: str
    model_used: str
    created_at: str

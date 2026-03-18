from pydantic import BaseModel


class HistoryMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    collection: str | None = None
    history: list[HistoryMessage] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    response_time_ms: int
    ram_used_mb: float
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

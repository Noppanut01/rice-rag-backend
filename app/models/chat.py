import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, func

from app.database import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSON, default=list)
    # experiment metrics
    model_used = Column(String)
    embedding_model = Column(String)
    retrieval_strategy = Column(String)
    chunk_size = Column(Integer)
    chunks_retrieved = Column(Integer)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

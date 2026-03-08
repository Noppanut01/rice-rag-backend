import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func

from app.database import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSON, default=list)
    # metrics สำหรับ experiment comparison
    model_used = Column(String)
    embedding_model = Column(String)
    retrieval_strategy = Column(String)
    chunk_size = Column(Integer)
    chunks_retrieved = Column(Integer)
    response_time_ms = Column(Integer)
    ram_used_mb = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

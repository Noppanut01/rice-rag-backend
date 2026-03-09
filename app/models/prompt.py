import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func

from app.database import Base


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

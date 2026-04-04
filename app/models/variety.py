import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, func

from app.database import Base


class RiceVariety(Base):
    __tablename__ = "rice_varieties"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    collection_name = Column(String, nullable=False, unique=True)
    harvest_age_days = Column(Integer, nullable=False)
    is_photoperiod_sensitive = Column(Boolean, default=False)
    supported_methods = Column(JSON, nullable=False, default=["transplant", "broadcast"])
    description = Column(String, nullable=True)
    reference_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

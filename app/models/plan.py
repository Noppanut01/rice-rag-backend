import uuid

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, JSON, String, func

from app.database import Base


class PlantingPlan(Base):
    __tablename__ = "planting_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    variety_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    area_rai = Column(Float, nullable=False)
    plot_name = Column(String, nullable=True)
    plan_content = Column(JSON, default=dict)
    response_time_ms = Column(Integer, nullable=True)
    ram_used_mb = Column(Float, nullable=True)
    model_used = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

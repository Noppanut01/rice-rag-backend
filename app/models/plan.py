import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, func

from app.database import Base


class PlantingPlan(Base):
    __tablename__ = "planting_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    variety_id = Column(String, nullable=False)
    variety_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    area_rai = Column(Float, nullable=False)
    plot_name = Column(String, nullable=True)
    planting_method = Column(String, nullable=False, default="transplant")
    soil_type = Column(String, nullable=True, default="clay")  # clay, loam, sandy
    created_at = Column(DateTime, server_default=func.now())


class PlanTask(Base):
    __tablename__ = "plan_tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String, ForeignKey("planting_plans.id", ondelete="CASCADE"), nullable=False)
    day = Column(Integer, nullable=False)
    stage = Column(String, nullable=False)
    task_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    is_completed = Column(Boolean, default=False)

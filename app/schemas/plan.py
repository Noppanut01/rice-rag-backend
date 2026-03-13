from datetime import date

from pydantic import BaseModel


class PlanTaskInput(BaseModel):
    day: int
    stage: str
    task_name: str
    description: str | None = None
    date: date


class PlanTaskResponse(BaseModel):
    id: str
    day: int
    stage: str
    task_name: str
    description: str | None
    date: str
    is_completed: bool


class PlanRequest(BaseModel):
    plot_name: str | None = None
    variety_id: str
    variety_name: str
    start_date: date
    area_rai: float


class PlanResponse(BaseModel):
    id: str
    variety_id: str
    variety_name: str
    start_date: str
    area_rai: float
    plot_name: str | None
    tasks: list[PlanTaskResponse]
    created_at: str

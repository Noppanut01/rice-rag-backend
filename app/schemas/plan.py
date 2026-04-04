from datetime import date

from pydantic import BaseModel


class PlanTaskResponse(BaseModel):
    id: str
    day: int
    stage: str
    task_name: str
    description: str | None
    date: str
    is_completed: bool


class PlanResources(BaseModel):
    seed_kg: float
    fertilizer1_kg: float
    fertilizer2_kg: float
    seedling_trays: int | None = None


class PlanRequest(BaseModel):
    plot_name: str | None = None
    variety_id: str
    start_date: date
    area_rai: float
    planting_method: str = "transplant"


class PlanResponse(BaseModel):
    id: str
    variety_id: str
    variety_name: str
    start_date: str
    area_rai: float
    plot_name: str | None
    planting_method: str
    resources: PlanResources
    tasks: list[PlanTaskResponse]
    created_at: str

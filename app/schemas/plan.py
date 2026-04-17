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
    fertilizer1_formula: str
    fertilizer2_kg: float
    fertilizer2_formula: str
    seedling_trays: int | None = None


class PlanRequest(BaseModel):
    plot_name: str | None = None
    variety_id: str
    start_date: date
    area_rai: float
    planting_method: str = "transplant"
    soil_type: str = "clay"  # clay=ดินเหนียว, loam=ดินร่วน, sandy=ดินทราย


class PlanUpdateRequest(BaseModel):
    plot_name: str | None = None
    area_rai: float | None = None
    soil_type: str | None = None


class PlanCloneRequest(BaseModel):
    start_date: date
    plot_name: str | None = None


class PlanResponse(BaseModel):
    id: str
    variety_id: str
    variety_name: str
    start_date: str
    actual_planting_date: str   # วันที่คาดว่าจะลงมือปลูกจริง (start_date + planting offset)
    area_rai: float
    plot_name: str | None
    planting_method: str
    soil_type: str
    is_photoperiod_sensitive: bool
    resources: PlanResources
    tasks: list[PlanTaskResponse]
    created_at: str

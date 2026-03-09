from datetime import date

from pydantic import BaseModel


class PlanRequest(BaseModel):
    plot_name: str | None = None
    variety_name: str
    start_date: date
    area_rai: float


class PlanResponse(BaseModel):
    id: str
    variety_name: str
    start_date: str
    area_rai: float
    plot_name: str | None
    plan_content: dict
    created_at: str

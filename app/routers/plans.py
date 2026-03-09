from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session

from app.dependencies import get_current_user, get_db
from app.models.plan import PlantingPlan
from app.schemas.plan import PlanRequest, PlanResponse
from app.services.plan_service import plan_service

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/", response_model=PlanResponse)
def create_plan(
    body: PlanRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = plan_service.generate_plan(
        variety_name=body.variety_name,
        start_date=body.start_date,
        area_rai=body.area_rai,
    )

    plan = PlantingPlan(
        user_id=current_user.id,
        variety_name=body.variety_name,
        start_date=body.start_date,
        area_rai=body.area_rai,
        plot_name=body.plot_name,
        plan_content={"answer": result["answer"], "sources": result["sources"]},
        response_time_ms=result["response_time_ms"],
        ram_used_mb=result["ram_used_mb"],
        model_used=result["model_used"],
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return PlanResponse(
        id=str(plan.id),
        variety_name=str(plan.variety_name),
        start_date=str(plan.start_date),
        area_rai=float(plan.area_rai),
        plot_name=str(plan.plot_name) if plan.plot_name else None,
        plan_content=plan.plan_content,
        created_at=str(plan.created_at),
    )


@router.get("/", response_model=list[PlanResponse])
def get_plans(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plans = db.query(PlantingPlan).filter(PlantingPlan.user_id == current_user.id).all()
    return [
        PlanResponse(
            id=str(p.id),
            variety_name=str(p.variety_name),
            start_date=str(p.start_date),
            area_rai=float(p.area_rai),
            plot_name=str(p.plot_name) if p.plot_name else None,
            plan_content=p.plan_content,
            created_at=str(p.created_at),
        )
        for p in plans
    ]

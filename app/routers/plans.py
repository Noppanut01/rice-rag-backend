from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm.session import Session

from app.dependencies import get_current_user, get_db
from app.models.plan import PlanTask, PlantingPlan
from app.models.variety import RiceVariety
from app.schemas.plan import PlanRequest, PlanResources, PlanResponse, PlanTaskResponse
from app.services.plan_service import plan_service

router = APIRouter(prefix="/plans", tags=["plans"])


def _task_response(t) -> PlanTaskResponse:
    return PlanTaskResponse(
        id=str(t.id),
        day=int(t.day),
        stage=str(t.stage),
        task_name=str(t.task_name),
        description=str(t.description) if t.description else None,
        date=str(t.date),
        is_completed=bool(t.is_completed),
    )


def _plan_response(p, tasks, resources: dict) -> PlanResponse:
    return PlanResponse(
        id=str(p.id),
        variety_id=str(p.variety_id),
        variety_name=str(p.variety_name),
        start_date=str(p.start_date),
        area_rai=float(p.area_rai),
        plot_name=str(p.plot_name) if p.plot_name else None,
        planting_method=str(p.planting_method),
        resources=PlanResources(**resources),
        tasks=[_task_response(t) for t in tasks],
        created_at=str(p.created_at),
    )


@router.post("/", response_model=PlanResponse)
def create_plan(
    body: PlanRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    variety = db.query(RiceVariety).filter(RiceVariety.id == body.variety_id).first()
    if not variety:
        raise HTTPException(status_code=404, detail="ไม่พบพันธุ์ข้าว")

    if body.planting_method not in variety.supported_methods:
        raise HTTPException(
            status_code=400,
            detail=f"พันธุ์ {variety.name} ไม่รองรับวิธีปลูก '{body.planting_method}'"
        )

    tasks, resources = plan_service.generate_plan(
        variety_name=str(variety.name),
        harvest_age_days=int(variety.harvest_age_days),
        planting_method=body.planting_method,
        start_date=body.start_date,
        area_rai=body.area_rai,
    )

    plan = PlantingPlan(
        user_id=current_user.id,
        variety_id=body.variety_id,
        variety_name=str(variety.name),
        start_date=body.start_date,
        area_rai=body.area_rai,
        plot_name=body.plot_name,
        planting_method=body.planting_method,
    )
    db.add(plan)
    db.flush()

    for t in tasks:
        db.add(PlanTask(
            plan_id=plan.id,
            day=t["day"],
            stage=t["stage"],
            task_name=t["task_name"],
            description=t["description"],
            date=t["date"],
        ))

    db.commit()
    db.refresh(plan)

    plan_tasks = db.query(PlanTask).filter(PlanTask.plan_id == plan.id).order_by(PlanTask.day).all()
    return _plan_response(plan, plan_tasks, resources)


@router.get("/", response_model=list[PlanResponse])
def get_plans(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.services.plan_service import _calculate_resources
    plans = db.query(PlantingPlan).filter(PlantingPlan.user_id == current_user.id).all()
    result = []
    for p in plans:
        tasks = db.query(PlanTask).filter(PlanTask.plan_id == p.id).order_by(PlanTask.day).all()
        resources = _calculate_resources(str(p.planting_method), float(p.area_rai))
        result.append(_plan_response(p, tasks, resources))
    return result


@router.patch("/{plan_id}/tasks/{task_id}/toggle", response_model=PlanTaskResponse)
def toggle_task(
    plan_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    plan = db.query(PlantingPlan).filter(
        PlantingPlan.id == plan_id,
        PlantingPlan.user_id == current_user.id,
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="ไม่พบแผน")

    task = db.query(PlanTask).filter(PlanTask.id == task_id, PlanTask.plan_id == plan_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="ไม่พบงาน")

    task.is_completed = not task.is_completed
    db.commit()
    db.refresh(task)
    return _task_response(task)


@router.delete("/{plan_id}", status_code=204)
def delete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    plan = db.query(PlantingPlan).filter(
        PlantingPlan.id == plan_id,
        PlantingPlan.user_id == current_user.id,
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="ไม่พบแผน")

    db.query(PlanTask).filter(PlanTask.plan_id == plan_id).delete()
    db.delete(plan)
    db.commit()

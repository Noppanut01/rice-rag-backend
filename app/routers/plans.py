from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm.session import Session

from app.dependencies import get_current_user, get_db
from app.models.plan import PlanTask, PlantingPlan
from app.schemas.plan import PlanRequest, PlanResponse, PlanTaskResponse
from app.services.plan_service import plan_service

router = APIRouter(prefix="/plans", tags=["plans"])


def _task_response(t: PlanTask) -> PlanTaskResponse:
    return PlanTaskResponse(
        id=str(t.id),
        day=int(t.day),
        stage=str(t.stage),
        task_name=str(t.task_name),
        description=str(t.description) if t.description else None,
        date=str(t.date),
        is_completed=bool(t.is_completed),
    )


def _plan_response(plan: PlantingPlan, db: Session) -> PlanResponse:
    tasks = db.query(PlanTask).filter(PlanTask.plan_id == plan.id).order_by(PlanTask.day).all()
    return PlanResponse(
        id=str(plan.id),
        variety_id=str(plan.variety_id),
        variety_name=str(plan.variety_name),
        start_date=str(plan.start_date),
        area_rai=float(plan.area_rai),
        plot_name=str(plan.plot_name) if plan.plot_name else None,
        tasks=[_task_response(t) for t in tasks],
        created_at=str(plan.created_at),
    )


@router.post("/", response_model=PlanResponse)
def create_plan(
    body: PlanRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tasks = plan_service.generate_plan(
        variety_name=body.variety_name,
        start_date=body.start_date,
        area_rai=body.area_rai,
    )

    plan = PlantingPlan(
        user_id=current_user.id,
        variety_id=body.variety_id,
        variety_name=body.variety_name,
        start_date=body.start_date,
        area_rai=body.area_rai,
        plot_name=body.plot_name,
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
    return _plan_response(plan, db)


@router.get("/", response_model=list[PlanResponse])
def get_plans(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plans = db.query(PlantingPlan).filter(PlantingPlan.user_id == current_user.id).all()
    return [_plan_response(p, db) for p in plans]


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

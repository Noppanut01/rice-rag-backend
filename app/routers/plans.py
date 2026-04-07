from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm.session import Session

from app.dependencies import get_current_user, get_db
from app.models.plan import PlanTask, PlantingPlan
from app.models.variety import RiceVariety
from app.schemas.plan import PlanRequest, PlanResources, PlanResponse, PlanTaskResponse
from app.services.plan_service import PLANTING_DAY, _calculate_resources, plan_service

router = APIRouter(prefix="/plans", tags=["plans"])

SOIL_FERT1_FORMULA = {
    "clay": "16-20-0",
    "loam": "16-16-8",
    "sandy": "16-16-8",
}


def _resolve_fert(variety: RiceVariety, soil_type: str) -> tuple[float, float, float, float, str, str, str, str]:
    """Returns (fert1_rate, fert1_max, fert2_rate, fert2_max, fert1_formula, fert2_formula, fert1_note, fert2_note)"""
    is_sensitive = bool(variety.is_photoperiod_sensitive)

    fert1_min = float(variety.fert1_rate_min) if variety.fert1_rate_min is not None else (20.0 if is_sensitive else 25.0)
    fert1_max = float(variety.fert1_rate_max) if variety.fert1_rate_max is not None else (25.0 if is_sensitive else 35.0)
    fert2_min = float(variety.fert2_rate_min) if variety.fert2_rate_min is not None else (5.0 if is_sensitive else 10.0)
    fert2_max = float(variety.fert2_rate_max) if variety.fert2_rate_max is not None else (10.0 if is_sensitive else 15.0)

    fert1_formula = str(variety.fert1_formula) if variety.fert1_formula else SOIL_FERT1_FORMULA.get(soil_type, "16-20-0")
    fert2_formula = str(variety.fert2_formula) if variety.fert2_formula else "46-0-0"

    fert1_note = str(variety.fert1_note) if variety.fert1_note else f"แนะนำ {int(fert1_min)}-{int(fert1_max)} กก./ไร่ ขึ้นอยู่กับสภาพดินและผลผลิตที่ต้องการ"
    fert2_note = str(variety.fert2_note) if variety.fert2_note else f"แนะนำ {int(fert2_min)}-{int(fert2_max)} กก./ไร่ ขึ้นอยู่กับสภาพดินและผลผลิตที่ต้องการ"

    return fert1_min, fert1_max, fert2_min, fert2_max, fert1_formula, fert2_formula, fert1_note, fert2_note


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

    h = int(variety.harvest_age_days)
    fert1_rate, _, fert2_rate, _, fert1_formula, fert2_formula, fert1_note, fert2_note = _resolve_fert(variety, body.soil_type)

    # ข้าวไวแสง: แปลง heading_calendar "MM-DD" → date object ของปีที่เหมาะสม
    heading_calendar_date: date | None = None
    if variety.heading_calendar:
        try:
            cal_m, cal_d = map(int, str(variety.heading_calendar).split("-"))
            hd = date(body.start_date.year, cal_m, cal_d)
            if hd <= body.start_date:
                hd = date(body.start_date.year + 1, cal_m, cal_d)
            heading_calendar_date = hd
        except (ValueError, TypeError):
            pass

    tasks, resources, actual_planting_date = plan_service.generate_plan(
        harvest_age_days=h,
        planting_method=body.planting_method,
        start_date=body.start_date,
        area_rai=body.area_rai,
        soil_type=body.soil_type,
        tillering_day=int(variety.tillering_day) if variety.tillering_day is not None else None,
        panicle_initiation_day=int(variety.panicle_initiation_day) if variety.panicle_initiation_day is not None else None,
        heading_day=int(variety.heading_day) if variety.heading_day is not None else None,
        fert1_rate=fert1_rate,
        fert2_rate=fert2_rate,
        fert1_formula=fert1_formula,
        fert1_note=fert1_note,
        fert2_note=fert2_note,
        heading_calendar_date=heading_calendar_date,
    )

    plan = PlantingPlan(
        user_id=current_user.id,
        variety_id=body.variety_id,
        variety_name=str(variety.name),
        start_date=body.start_date,
        area_rai=body.area_rai,
        plot_name=body.plot_name,
        planting_method=body.planting_method,
        soil_type=body.soil_type,
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
    return PlanResponse(
        id=str(plan.id),
        variety_id=str(plan.variety_id),
        variety_name=str(plan.variety_name),
        start_date=str(plan.start_date),
        actual_planting_date=str(actual_planting_date),
        area_rai=float(plan.area_rai),
        plot_name=str(plan.plot_name) if plan.plot_name else None,
        planting_method=str(plan.planting_method),
        soil_type=str(plan.soil_type) if plan.soil_type else "clay",
        resources=PlanResources(**resources),
        tasks=[
            PlanTaskResponse(
                id=str(t.id),
                day=int(t.day),
                stage=str(t.stage),
                task_name=str(t.task_name),
                description=str(t.description) if t.description else None,
                date=str(t.date),
                is_completed=bool(t.is_completed),
            )
            for t in plan_tasks
        ],
        created_at=str(plan.created_at),
    )


@router.get("/", response_model=list[PlanResponse])
def get_plans(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plans = db.query(PlantingPlan).filter(PlantingPlan.user_id == current_user.id).all()
    result = []
    for p in plans:
        tasks = db.query(PlanTask).filter(PlanTask.plan_id == p.id).order_by(PlanTask.day).all()
        variety = db.query(RiceVariety).filter(RiceVariety.id == p.variety_id).first()
        soil_type = str(p.soil_type) if p.soil_type else "clay"
        fert1_rate, _, fert2_rate, _, fert1_formula, _, _, _ = _resolve_fert(variety, soil_type) if variety else (25.0, 35.0, 10.0, 15.0, "", "46-0-0", "", "")
        resources = _calculate_resources(str(p.planting_method), float(p.area_rai), soil_type, fert1_rate, fert2_rate, fert1_formula)
        p_offset = PLANTING_DAY.get(str(p.planting_method), 0)
        actual_planting_date = p.start_date + timedelta(days=p_offset)
        result.append(PlanResponse(
            id=str(p.id),
            variety_id=str(p.variety_id),
            variety_name=str(p.variety_name),
            start_date=str(p.start_date),
            actual_planting_date=str(actual_planting_date),
            area_rai=float(p.area_rai),
            plot_name=str(p.plot_name) if p.plot_name else None,
            planting_method=str(p.planting_method),
            soil_type=soil_type,
            resources=PlanResources(**resources),
            tasks=[
                PlanTaskResponse(
                    id=str(t.id),
                    day=int(t.day),
                    stage=str(t.stage),
                    task_name=str(t.task_name),
                    description=str(t.description) if t.description else None,
                    date=str(t.date),
                    is_completed=bool(t.is_completed),
                )
                for t in tasks
            ],
            created_at=str(p.created_at),
        ))
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
    return PlanTaskResponse(
        id=str(task.id),
        day=int(task.day),
        stage=str(task.stage),
        task_name=str(task.task_name),
        description=str(task.description) if task.description else None,
        date=str(task.date),
        is_completed=bool(task.is_completed),
    )


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
